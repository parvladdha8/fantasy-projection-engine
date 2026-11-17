import math, sys
from PIL import Image, ImageDraw
BLUE=(0,113,227,255); WHITE=(255,255,255,255); GREEN=(31,138,59,255)
def football(size, tile=True, pad=0.0):
    N=1024; im=Image.new("RGBA",(N,N),(0,0,0,0)); d=ImageDraw.Draw(im)
    if tile: d.rounded_rectangle([0,0,N-1,N-1], radius=int(N*0.22), fill=BLUE)
    cx,cy=N/2,N/2; a=N*(0.44-pad); b=N*(0.25-pad*0.6)    # half-length, half-height
    R=(a*a+b*b)/(2*b); off=R-b
    pts=[]
    th=math.asin(a/R)
    for i in range(201):  # top arc (circle centred below), then bottom arc
        t=-th+2*th*i/200; pts.append((cx+R*math.sin(t), cy+off-R*math.cos(t)))
    for i in range(201):
        t=th-2*th*i/200; pts.append((cx+R*math.sin(t), cy-off+R*math.cos(t)))
    # slight tilt for a livelier look
    ang=math.radians(-18)
    pts=[(cx+(x-cx)*math.cos(ang)-(y-cy)*math.sin(ang), cy+(x-cx)*math.sin(ang)+(y-cy)*math.cos(ang)) for x,y in pts]
    d.polygon(pts, fill=WHITE)
    def rot(x,y): return (cx+(x-cx)*math.cos(ang)-(y-cy)*math.sin(ang), cy+(x-cx)*math.sin(ang)+(y-cy)*math.cos(ang))
    w=int(N*0.035); L=a*0.42
    d.line([rot(cx-L,cy),rot(cx+L,cy)], fill=GREEN, width=w)
    for k in range(-2,3):
        x=cx+k*L/2.2; h=b*0.36
        d.line([rot(x,cy-h),rot(x,cy+h)], fill=GREEN, width=w)
    # green end stripes
    for s in (-1,1):
        x=cx+s*a*0.70; h=b*0.62
        d.line([rot(x,cy-h),rot(x,cy+h)], fill=GREEN, width=int(w*1.1))
    return im.resize((size,size), Image.LANCZOS)
out=sys.argv[1]
football(512).save(f"{out}/football-512.png")
football(192).save(f"{out}/icon.png")
football(180).save(f"{out}/apple-icon.png")
football(48).save(f"{out}/favicon.ico", sizes=[(16,16),(32,32),(48,48)])
football(1024).resize((64,64),Image.LANCZOS).save(f"{out}/preview-64.png")
# preview sheet
sheet=Image.new("RGBA",(560,140),(255,255,255,255))
x=10
for s in (128,64,32,16):
    sheet.paste(football(1024).resize((s,s),Image.LANCZOS),(x,(140-s)//2),football(1024).resize((s,s),Image.LANCZOS)); x+=s+30
dark=Image.new("RGBA",(140,140),(0,0,0,255)); im=football(1024).resize((96,96),Image.LANCZOS); dark.paste(im,(22,22),im)
sheet.paste(dark,(410,0)); sheet.save(f"{out}/sheet.png")
