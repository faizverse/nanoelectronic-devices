"""Shrink a PDF's oversized images for the web copy (the originals on the Mac are untouched).

Usage: python3 pdfshrink.py in.pdf out.pdf [max_ppi=250] [jpeg_quality=85]
- Images drawn at more than max_ppi are downsampled to max_ppi (placement measured from the page content).
- Photo-like images (JPEG at least 3x smaller than lossless) become JPEG; diagrams stay lossless (Flate).
- Images with a soft mask or an unusual colour space are left alone. A new stream is kept only if it is smaller.
"""
import sys, io, zlib
import pikepdf
from pikepdf import PdfImage, Name
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
MAXPPI = float(sys.argv[3]) if len(sys.argv) > 3 else 250
Q = int(sys.argv[4]) if len(sys.argv) > 4 else 85

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
        raw = img.tobytes(); flate = zlib.compress(raw, 9)
        jb = io.BytesIO(); img.save(jb, "JPEG", quality=Q, optimize=True, subsampling=0); jpg = jb.getvalue()
        if len(jpg) * 3 <= len(flate): data, filt = jpg, Name.DCTDecode
        else: data, filt = flate, Name.FlateDecode
        if len(data) >= old: after += old; continue
        x.write(data, filter=filt)
        x.Width, x.Height, x.BitsPerComponent = img.width, img.height, 8
        if "/DecodeParms" in x: del x["/DecodeParms"]
        if cs is None: x.ColorSpace = Name.DeviceGray if img.mode == "L" else Name.DeviceRGB
        if "/Decode" in x: del x["/Decode"]
        after += len(data)

pdf.remove_unreferenced_resources()
pdf.save(dst, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
print(f"{src}: images {before/1e6:.1f} -> {after/1e6:.1f} MB")
