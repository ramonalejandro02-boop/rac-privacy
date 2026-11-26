<!doctype html>
<html><head><meta charset="utf-8">
<style>
@font-face{font-family:'Anton';src:url(fonts/barlow-800.woff2)}
@font-face{font-family:'Elite';src:url(fonts/jbmono-600.woff2)}
@font-face{font-family:'Play';src:url(fonts/playfair-display-latin-900-normal.woff2);font-weight:900}
@font-face{font-family:'Arch';src:url(fonts/archivo-black-latin-400-normal.woff2)}
html,body{margin:0;background:#000}canvas{display:block}
</style></head><body>
<canvas id="c" width="1080" height="1920"></canvas>
<script>
const W=1080,H=1920;
const cv=document.getElementById('c'),g=cv.getContext('2d');
let TL,EV,PAPER,HITS=[];
const INK='#eaf4ff',PAPERC='#0f4c81',RED='#ff7a59',BLUE='#5fb4ff',LBLUE='#9fd8ff',GREY='#5d7fa3',GREEN='#5fe3a1',YEL='#ffd23f',NAVY='#0a2f55',PANEL='#0e3d6e';
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const ease=x=>{x=clamp(x);return 1-Math.pow(1-x,3)};
const eio=x=>{x=clamp(x);return x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2};
const back=x=>{x=clamp(x);const c1=1.9,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2)};
const lerp=(a,b,t)=>a+(b-a)*t;
const k=(t,at,d=.35)=>clamp((t-at)/d);
function rnd(s){let x=Math.sin(s*999.13)*43758.5453;return x-Math.floor(x);}
const GOLD='#ffd23f',AMB='#ffae42',CREAM='rgba(14,61,110,.92)';
function makePaper(){const c=document.createElement('canvas');c.width=W;c.height=H;const p=c.getContext('2d');
  const gr=p.createLinearGradient(0,0,0,H);gr.addColorStop(0,'#11558f');gr.addColorStop(1,'#0b3a66');p.fillStyle=gr;p.fillRect(0,0,W,H);
  p.strokeStyle='rgba(255,255,255,.06)';p.lineWidth=1;for(let x=0;x<=W;x+=30){p.beginPath();p.moveTo(x+.5,0);p.lineTo(x+.5,H);p.stroke();}for(let y=0;y<=H;y+=30){p.beginPath();p.moveTo(0,y+.5);p.lineTo(W,y+.5);p.stroke();}
  p.strokeStyle='rgba(255,255,255,.13)';for(let x=0;x<=W;x+=150){p.beginPath();p.moveTo(x+.5,0);p.lineTo(x+.5,H);p.stroke();}for(let y=0;y<=H;y+=150){p.beginPath();p.moveTo(0,y+.5);p.lineTo(W,y+.5);p.stroke();}
  const id=p.getImageData(0,0,W,H),d=id.data;for(let i=0;i<d.length;i+=4){const n=(Math.random()-.5)*8;d[i]+=n;d[i+1]+=n;d[i+2]+=n;}p.putImageData(id,0,0);
  const v=p.createRadialGradient(W/2,H/2,H*.3,W/2,H/2,H*.75);v.addColorStop(0,'rgba(0,0,0,0)');v.addColorStop(1,'rgba(0,10,30,.45)');p.fillStyle=v;p.fillRect(0,0,W,H);
  p.strokeStyle='rgba(234,244,255,.7)';p.lineWidth=3;p.strokeRect(30,30,W-60,H-60);p.lineWidth=1;p.strokeRect(42,42,W-84,H-84);return c;}
function T(s,x,y,fs,font='Anton',col=INK,align='center',base='middle'){g.font=`${font==='Play'?'900 ':''}${fs}px ${font}`;g.textAlign=align;g.textBaseline=base;g.fillStyle=col;g.fillText(s,x,y);}
function fitT(s,x,y,fs,maxW,font='Anton',col=INK,align='center'){g.font=`${font==='Play'?'900 ':''}${fs}px ${font}`;const w=g.measureText(s).width;if(w>maxW)fs*=maxW/w;T(s,x,y,fs,font,col,align);}
function shadowed(fn,off=10,a=.25){g.save();g.shadowColor=`rgba(40,25,0,${a})`;g.shadowOffsetX=off*.5;g.shadowOffsetY=off;g.shadowBlur=off*1.4;fn();g.restore();}
function rr(x,y,w,h,r){g.beginPath();g.roundRect(x,y,w,h,r);}
function tape(x,y,rot,w=130){g.save();g.translate(x,y);g.rotate(rot);g.fillStyle='rgba(240,225,170,.85)';g.fillRect(-w/2,-20,w,40);g.strokeStyle='rgba(150,130,80,.3)';g.strokeRect(-w/2,-20,w,40);g.restore();}
function note(cx,cy,w,h,rot,sc,fill='#fbf7ec'){g.save();g.translate(cx,cy);g.rotate(rot);g.scale(sc,sc);shadowed(()=>{g.fillStyle=fill;g.fillRect(-w/2,-h/2,w,h);},14,.3);g.restore();}
function stamp(s,cx,cy,fs,rot,t,at,col=RED){
  if(t<at)return;const p=clamp((t-at)/.18);const sc=lerp(2.4,1,ease(p));
  g.save();g.translate(cx,cy);g.rotate(rot);g.scale(sc,sc);g.globalAlpha*=lerp(0,.92,p);
  g.font=`${fs}px Anton`;const w=g.measureText(s).width+80,h=fs*1.35;
  g.strokeStyle=col;g.lineWidth=10;rr(-w/2,-h/2,w,h,14);g.stroke();g.lineWidth=4;rr(-w/2+12,-h/2+12,w-24,h-24,8);g.stroke();
  T(s,0,fs*.04,fs,'Anton',col);
  // grunge holes
  g.fillStyle='rgba(15,76,129,.9)';const hs=Math.min(1,fs/80);
  for(let i=0;i<45;i++){g.beginPath();g.arc((rnd(i+fs)-.5)*w,(rnd(i*3+fs)-.5)*h,(1+rnd(i*7)*3)*hs,0,7);g.fill();}
  g.restore();
}
function marker(x,y,w,h,p,col='rgba(255,210,63,.85)'){if(p<=0)return;g.save();g.fillStyle=col;g.beginPath();const ww=w*p;g.moveTo(x,y+4);g.lineTo(x+ww,y);g.lineTo(x+ww-6,y+h);g.lineTo(x+4,y+h-3);g.closePath();g.fill();g.restore();}
function pin(x,y,p,col=RED){if(p<=0)return;const yy=y-lerp(160,0,ease(p))+ (p<1?Math.sin(p*9)*6*(1-p):0);
  g.save();g.translate(x,yy);g.scale(1.15,1.15);
  g.fillStyle='rgba(0,0,0,.25)';g.beginPath();g.ellipse(4,4,14*ease(p),5,0,0,7);g.fill();
  g.fillStyle=col;g.beginPath();g.moveTo(0,0);g.bezierCurveTo(-30,-38,-26,-70,0,-70);g.bezierCurveTo(26,-70,30,-38,0,0);g.fill();
  g.strokeStyle=INK;g.lineWidth=4;g.stroke();g.fillStyle='#fff';g.beginPath();g.arc(0,-46,10,0,7);g.fill();g.restore();}
function label(s,x,y,p,bg=INK,fg='#fff',fs=40,rot=-.03){if(p<=0)return;g.save();g.translate(x,y);g.rotate(rot);const sc=back(p);g.scale(sc,sc);g.font=`${fs}px Anton`;const w=g.measureText(s).width+40;
  shadowed(()=>{g.fillStyle=bg;g.fillRect(-w/2,-fs*.7,w,fs*1.4);},8,.3);T(s,0,fs*.03,fs,'Anton',fg);g.restore();}
function check(x,y,s,p,col=GREEN){if(p<=0)return;g.save();g.translate(x,y);g.strokeStyle=col;g.lineWidth=s*.16;g.lineCap='round';g.lineJoin='round';g.beginPath();
  const pts=[[-s*.4,0],[-s*.12,s*.3],[s*.45,-s*.38]];const p1=clamp(p*2),p2=clamp(p*2-1);
  g.moveTo(...pts[0]);g.lineTo(lerp(pts[0][0],pts[1][0],p1),lerp(pts[0][1],pts[1][1],p1));if(p2>0)g.lineTo(lerp(pts[1][0],pts[2][0],p2),lerp(pts[1][1],pts[2][1],p2));g.stroke();g.restore();}
function arrow(x1,y1,x2,y2,p,col=INK,lw=8){if(p<=0)return;const x=lerp(x1,x2,ease(p)),y=lerp(y1,y2,ease(p));g.save();g.strokeStyle=col;g.fillStyle=col;g.lineWidth=lw;g.lineCap='round';g.setLineDash([18,14]);g.beginPath();g.moveTo(x1,y1);g.lineTo(x,y);g.stroke();g.setLineDash([]);
  const a=Math.atan2(y2-y1,x2-x1);g.translate(x,y);g.rotate(a);g.beginPath();g.moveTo(10,0);g.lineTo(-24,-18);g.lineTo(-24,18);g.closePath();g.fill();g.restore();}

// ---------- map ----------
