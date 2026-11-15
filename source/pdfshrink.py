"""Shrink a PDF's oversized images for the web copy (the originals on the Mac are untouched).

Usage: python3 pdfshrink.py in.pdf out.pdf [max_ppi=250] [jpeg_quality=85] [pal]
- Images drawn at more than max_ppi are downsampled to max_ppi (placement measured from the page content).
- Photo-like images (JPEG at least 3x smaller than lossless) become JPEG; diagrams stay lossless (Flate).
- Images with a soft mask or an unusual colour space are left alone. A new stream is kept only if it is smaller.
- With "pal": a colour diagram may instead be stored as a 256-colour palette image (lossless when it has 256 colours
  or fewer), used only when that is smallest and stays within 45 dB PSNR of the original (visually identical).
"""
import sys, io, zlib
import pikepdf
from pikepdf import PdfImage, Name
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
MAXPPI = float(sys.argv[3]) if len(sys.argv) > 3 else 250
Q = int(sys.argv[4]) if len(sys.argv) > 4 else 85
PAL = len(sys.argv) > 5 and sys.argv[5] == "pal"


def png_flate(img):
    """Lossless Flate data with PNG row predictors, as a PNG file stores it (much smaller than plain Flate for diagrams).
    Returns (data, DecodeParms) for the PDF image stream."""
    import struct
    b = io.BytesIO(); img.save(b, "PNG", optimize=True); png = b.getvalue()
    pos, idat = 8, b""
    while pos < len(png):
        n, typ = struct.unpack(">I4s", png[pos:pos + 8])
        if typ == b"IDAT": idat += png[pos + 8:pos + 8 + n]
        pos += 12 + n
    colors = 1 if img.mode == "L" else 3
    return idat, pikepdf.Dictionary(Predictor=15, Colors=colors, BitsPerComponent=8, Columns=img.width)

def png_chunks(png):
    import struct
    pos, out = 8, {}
    while pos < len(png):
        n, typ = struct.unpack(">I4s", png[pos:pos + 8]); out.setdefault(typ, b""); out[typ] += png[pos + 8:pos + 8 + n]; pos += 12 + n
    return out

def palette_flate(img):
    """A 256-colour (or fewer) palette version of an RGB image: (data, DecodeParms, ColorSpace, BitsPerComponent, psnr)."""
    import struct, numpy as np
    q = img.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    a = np.asarray(img, float); b = np.asarray(q.convert("RGB"), float); mse = ((a - b) ** 2).mean()
    psnr = 99 if mse == 0 else 10 * np.log10(255 ** 2 / mse)
    bio = io.BytesIO(); q.save(bio, "PNG", optimize=True); ch = png_chunks(bio.getvalue())
    w, h, bits, ctype = struct.unpack(">IIBB", ch[b"IHDR"][:10]); assert ctype == 3
    plte = ch[b"PLTE"]; n = len(plte) // 3
    cs = pikepdf.Array([Name.Indexed, Name.DeviceRGB, n - 1, pikepdf.String(plte)])
    return ch[b"IDAT"], pikepdf.Dictionary(Predictor=15, Colors=1, BitsPerComponent=bits, Columns=w), cs, bits, psnr

pdf = pikepdf.open(src)

# Largest drawn size (in points) of each image XObject, from the cm matrix in force at each Do.
drawn = {}
def walk(content_owner, resources, ctm=(1, 0, 0, 1, 0, 0)):
    stack, cur = [], ctm
    xobjs = resources.get("/XObject", {}) if resources is not None else {}
    for operands, op in pikepdf.parse_content_stream(content_owner):
        o = str(op)
        if o == "q": stack.append(cur)
        elif o == "Q": cur = stack.pop() if stack else cur
        elif o == "cm":
            a, b, c, d, e, f = [float(x) for x in operands]
            A, B, C, D, E, F = cur
            cur = (a*A + b*C, a*B + b*D, c*A + d*C, c*B + d*D, e*A + f*C + E, e*B + f*D + F)
        elif o == "Do":
            x = xobjs.get(operands[0])
            if x is None: continue
            if x.get("/Subtype") == "/Image":
                w = (cur[0]**2 + cur[1]**2) ** .5; h = (cur[2]**2 + cur[3]**2) ** .5
                key = x.objgen; ow, oh = drawn.get(key, (0, 0)); drawn[key] = (max(ow, w), max(oh, h))
            elif x.get("/Subtype") == "/Form":
                walk(x, x.get("/Resources"), cur)

for page in pdf.pages:
    walk(page, page.get("/Resources"))

before = after = 0
for page in pdf.pages:
    for name, x in list(page.images.items()):
        if x.objgen not in drawn or "/SMask" in x or "/Mask" in x: continue
        cs = x.get("/ColorSpace")
        try:
            img = PdfImage(x).as_pil_image()
        except Exception:
            continue
        if img.mode not in ("RGB", "L"): continue
        wpt, hpt = drawn[x.objgen]
        ppi = img.width / (wpt / 72) if wpt else 0
        old = len(x.read_raw_bytes()); before += old
        if ppi > MAXPPI:
            s = MAXPPI / ppi
            img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
        flate, parms = png_flate(img)
        jb = io.BytesIO(); img.save(jb, "JPEG", quality=Q, optimize=True, subsampling=0); jpg = jb.getvalue()
        if len(jpg) * 3 <= len(flate): data, filt = jpg, Name.DCTDecode
        else: data, filt = flate, Name.FlateDecode
        newcs, bpc = None, 8
        if PAL and img.mode == "RGB":
            pdata, pparms, pcs, pbits, psnr = palette_flate(img)
            if psnr >= 45 and len(pdata) < len(data): data, filt, parms, newcs, bpc = pdata, Name.FlateDecode, pparms, pcs, pbits
        if len(data) >= old: after += old; continue
        x.write(data, filter=filt, decode_parms=(parms if filt == Name.FlateDecode else None))
        x.Width, x.Height, x.BitsPerComponent = img.width, img.height, bpc
        if newcs is not None: x.ColorSpace = newcs
        elif cs is None: x.ColorSpace = Name.DeviceGray if img.mode == "L" else Name.DeviceRGB
        if "/Decode" in x: del x["/Decode"]
        after += len(data)

pdf.remove_unreferenced_resources()
pdf.save(dst, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
print(f"{src}: images {before/1e6:.1f} -> {after/1e6:.1f} MB")
