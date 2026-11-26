
async function setup(tl){TL=tl;EV=tl.ev;
  await Promise.all(['Anton','Elite','Arch'].map(f=>document.fonts.load(`40px ${f}`)));await document.fonts.load('900 40px Play');PAPER=makePaper();}
// ---------- subtitles ----------
function chunks(sc){const out=[];let cur=[];sc.sub.forEach(w=>{cur.push(w);if(cur.length>=4){out.push(cur);cur=[];}});if(cur.length)out.push(cur);return out;}
let CH=null;
function subs(t,si){if(!CH)CH=TL.scenes.map(chunks);let cur=null;for(const c of CH[si])if(t>=c[0][0]-.05)cur=c;if(!cur||t>cur[cur.length-1][1]+.6)return;
  const fs0=74;g.font=`${fs0}px Anton`;const words=cur.map(w=>w[2].toUpperCase());const sp=22;
  let tw=words.reduce((a,w)=>a+g.measureText(w).width,0)+sp*(words.length-1);const fs=tw>960?fs0*960/tw:fs0;g.font=`${fs}px Anton`;tw=words.reduce((a,w)=>a+g.measureText(w).width,0)+sp*(words.length-1);
  let x=W/2-tw/2;const y=1470;g.save();g.globalAlpha=k(t,cur[0][0]-.05,.12);
  words.forEach((w,i)=>{const ww=g.measureText(w).width;const on=t>=cur[i][0]-.03&&(i==words.length-1||t<cur[i+1][0]-.03);
    if(on)marker(x-12,y-fs*.62,ww+24,fs*1.18,1);g.lineWidth=10;g.strokeStyle=PAPERC;g.lineJoin='round';g.font=`${fs}px Anton`;g.textAlign='left';g.textBaseline='middle';
    if(!on)g.strokeText(w,x,y);T(w,x,y,fs,'Anton',INK,'left');x+=ww+sp;});g.restore();}
function chrome(t){g.fillStyle=RED;g.fillRect(60,262,360,64);T('NOTICIA EXPLICADA',240,296,40,'Anton','#fff');
  g.fillStyle=INK;g.fillRect(60,336,960,5);g.fillRect(60,346,960,2);
  g.fillStyle='rgba(0,0,0,.12)';g.fillRect(60,1580,960,8);g.fillStyle=RED;g.fillRect(60,1580,960*clamp(t/TL.total),8);}
function sceneAt(t){let si=0;TL.scenes.forEach((s,i)=>{if(t>=s.start)si=i;});return si;}
function enter(t,at){const p=ease(k(t,at,.4));g.translate((1-p)*W*.5,0);g.translate(W/2,H/2);g.rotate((1-p)*.06);g.translate(-W/2,-H/2);g.globalAlpha=clamp(p*1.5);}
function shake(t){let x=0,y=0;HITS.forEach(h=>{const d=t-h;if(d>0&&d<.5){const a=Math.exp(-d*9)*14;x+=Math.sin(d*70)*a;y+=Math.cos(d*55)*a*.8;}});return [x,y];}
// ---------- objects ----------
const sub_=s=>s;
function kicker(s,y,p=1){if(p<=0)return;g.save();g.globalAlpha*=p;T(s,W/2,y,36,'Elite',INK);g.restore();}
function headline(s,y,fs,col,p,font='Anton',maxW=960){if(p<=0)return;g.save();g.translate(W/2,y);const sc=back(p);g.scale(sc,sc);fitT(s,0,0,fs,maxW,font,col);g.restore();}
function num(s,x,y,fs,col=INK,font='Anton'){T(s,x,y,fs,font,col);}
function bill(x,y,rot,s,col='#5fb37a',alpha=1){g.save();g.translate(x,y);g.rotate(rot);g.scale(s,s);g.globalAlpha*=alpha;
  shadowed(()=>{g.fillStyle=col;g.fillRect(-110,-55,220,110);},6,.25);g.strokeStyle='rgba(0,0,0,.35)';g.lineWidth=4;g.strokeRect(-96,-42,192,84);
  g.fillStyle='rgba(0,0,0,.2)';g.beginPath();g.arc(0,0,30,0,7);g.fill();T('L',0,3,46,'Anton','rgba(255,255,255,.9)');T('100',-68,-24,22,'Anton','rgba(0,0,0,.4)');T('100',68,24,22,'Anton','rgba(0,0,0,.4)');g.restore();}
function coin(x,y,r,spin=0,alpha=1){g.save();g.translate(x,y);g.globalAlpha*=alpha;const sx=Math.abs(Math.cos(spin))*.85+.15;g.scale(sx,1);
  g.fillStyle='#a87412';g.beginPath();g.arc(0,r*.12,r,0,7);g.fill();g.fillStyle=GOLD;g.beginPath();g.arc(0,0,r,0,7);g.fill();g.strokeStyle=INK;g.lineWidth=Math.max(2,r*.1);g.stroke();
  g.strokeStyle='#a87412';g.lineWidth=r*.1;g.beginPath();g.arc(0,0,r*.7,0,7);g.stroke();if(sx>.4)T('L',0,2,r*1.05,'Anton',INK);g.restore();}
function bag(x,y,s,sq=0){g.save();g.translate(x,y);g.scale(s*(1+sq*.12),s*(1-sq*.12));
  shadowed(()=>{g.fillStyle='#d9b36a';g.beginPath();g.moveTo(-60,-120);g.quadraticCurveTo(0,-80,60,-120);g.lineTo(40,-80);g.quadraticCurveTo(170,0,130,90);g.quadraticCurveTo(0,150,-130,90);g.quadraticCurveTo(-170,0,-40,-80);g.closePath();g.fill();},12,.3);
  g.strokeStyle=INK;g.lineWidth=7;g.stroke();g.fillStyle=INK;g.fillRect(-50,-95,100,20);T('L',0,25,130,'Anton',INK);g.restore();}
function confetti(t,at,cx,cy,n=60){const d=t-at;if(d<0||d>2.2)return;for(let i=0;i<n;i++){const a=rnd(i)*6.28,v=380+rnd(i+9)*520;const x=cx+Math.cos(a)*v*d,y=cy+Math.sin(a)*v*d*.7+700*d*d;
  g.save();g.translate(x,y);g.rotate(d*8+i);g.globalAlpha*=clamp(1-d/2.2);g.fillStyle=[RED,GOLD,BLUE,GREEN,INK][i%5];g.fillRect(-9,-5,18,10);g.restore();}}
function person(x,y,on,jump){g.save();g.translate(x,y-jump);g.fillStyle=on?GREEN:'rgba(27,26,23,.18)';g.beginPath();g.arc(0,-14,17,0,7);g.fill();g.beginPath();g.ellipse(0,26,26,20,0,Math.PI,0);g.fill();
  if(on){g.strokeStyle=INK;g.lineWidth=3;g.beginPath();g.arc(0,-14,17,0,7);g.stroke();}g.restore();}
function ring(cx,cy,r,lw,p,col,p0=0){if(p<=.001)return;g.save();g.lineCap='butt';g.strokeStyle=col;g.lineWidth=lw;g.beginPath();g.arc(cx,cy,r,-Math.PI/2+p0*2*Math.PI,-Math.PI/2+(p0+p)*2*Math.PI);g.stroke();g.restore();}
function ringBase(cx,cy,r,lw){g.save();g.strokeStyle=INK;g.lineWidth=4;g.beginPath();g.arc(cx,cy,r+lw/2,0,7);g.stroke();g.beginPath();g.arc(cx,cy,r-lw/2,0,7);g.stroke();
  g.strokeStyle='rgba(27,26,23,.08)';g.lineWidth=lw;g.beginPath();g.arc(cx,cy,r,0,7);g.stroke();g.restore();}
function paperCard(cx,cy,w,h,rot,sc=1,fill=CREAM){g.save();g.translate(cx,cy);g.rotate(rot);g.scale(sc,sc);shadowed(()=>{g.fillStyle=fill;g.fillRect(-w/2,-h/2,w,h);},14,.3);g.restore();}
function hand(x,y,press){g.save();g.translate(x,y);g.scale(1-press*.12,1-press*.12);g.fillStyle='#fff';g.strokeStyle=INK;g.lineWidth=5;
  g.beginPath();g.moveTo(0,0);g.lineTo(0,-70);g.quadraticCurveTo(0,-84,13,-84);g.quadraticCurveTo(26,-84,26,-70);g.lineTo(26,-30);g.lineTo(70,-20);g.quadraticCurveTo(86,-14,82,6);g.lineTo(70,60);g.lineTo(10,60);g.lineTo(-24,10);g.quadraticCurveTo(-30,-6,-14,-8);g.closePath();g.fill();g.stroke();g.restore();}
function ambient(t){for(let i=0;i<12;i++){const x=rnd(i)*W,sp=20+rnd(i+3)*30,y=((rnd(i+7)*H)-(t*sp))%H;coin(x,y<0?y+H:y,10+rnd(i+1)*10,t*2+i,.1);}}


// ---- blueprint overrides ----
function shadowed(fn){const fr=g.fillRect.bind(g);g.save();g.fillRect=function(x,y,w,h){fr(x,y,w,h);g.save();g.strokeStyle=INK;g.lineWidth=3;g.strokeRect(x,y,w,h);g.restore();};fn();g.fillRect=CanvasRenderingContext2D.prototype.fillRect;g.restore();}
function tape(x,y,rot,w=130){g.save();g.translate(x,y);g.rotate(rot);g.strokeStyle=YEL;g.lineWidth=4;g.beginPath();g.moveTo(-28,0);g.lineTo(28,0);g.moveTo(0,-28);g.lineTo(0,28);g.stroke();g.beginPath();g.arc(0,0,14,0,7);g.stroke();g.restore();}
function hand(x,y,press){g.save();g.translate(x,y);g.scale(1-press*.12,1-press*.12);g.fillStyle=PANEL;g.strokeStyle=INK;g.lineWidth=5;
  g.beginPath();g.moveTo(0,0);g.lineTo(0,-70);g.quadraticCurveTo(0,-84,13,-84);g.quadraticCurveTo(26,-84,26,-70);g.lineTo(26,-30);g.lineTo(70,-20);g.quadraticCurveTo(86,-14,82,6);g.lineTo(70,60);g.lineTo(10,60);g.lineTo(-24,10);g.quadraticCurveTo(-30,-6,-14,-8);g.closePath();g.fill();g.stroke();g.restore();}
function label(s,x,y,p,bg=NAVY,fg='#fff',fs=40,rot=-.03){if(p<=0)return;if(bg===INK)bg=NAVY;if(fg===INK)fg='#fff';g.save();g.translate(x,y);g.rotate(rot);const sc=back(p);g.scale(sc,sc);g.font=`${fs}px Anton`;const w=g.measureText(s).width+44;
  g.fillStyle=bg;g.fillRect(-w/2,-fs*.72,w,fs*1.44);g.strokeStyle=INK;g.lineWidth=3;g.strokeRect(-w/2,-fs*.72,w,fs*1.44);
  g.strokeStyle=INK;g.lineWidth=2;[[-w/2,-fs*.72],[w/2,-fs*.72],[-w/2,fs*.72],[w/2,fs*.72]].forEach(([a,b])=>{g.beginPath();g.moveTo(a-12,b);g.lineTo(a+12,b);g.moveTo(a,b-12);g.lineTo(a,b+12);g.stroke();});
  T(s,0,fs*.03,fs,'Anton',fg);g.restore();}
function subs(t,si){if(!CH)CH=TL.scenes.map(chunks);let cur=null;for(const c of CH[si])if(t>=c[0][0]-.05)cur=c;if(!cur||t>cur[cur.length-1][1]+.6)return;
  const fs0=78;g.font=`${fs0}px Anton`;const words=cur.map(w=>w[2].toUpperCase());const sp=22;
  let tw=words.reduce((a,w)=>a+g.measureText(w).width,0)+sp*(words.length-1);const fs=tw>960?fs0*960/tw:fs0;g.font=`${fs}px Anton`;tw=words.reduce((a,w)=>a+g.measureText(w).width,0)+sp*(words.length-1);
  let x=W/2-tw/2;const y=1470;g.save();g.globalAlpha=k(t,cur[0][0]-.05,.12);
  words.forEach((w,i)=>{const ww=g.measureText(w).width;const on=t>=cur[i][0]-.03&&(i==words.length-1||t<cur[i+1][0]-.03);
    if(on){g.fillStyle=LBLUE;g.fillRect(x-12,y-fs*.6,ww+24,fs*1.16);}T(w,x,y,fs,'Anton',on?NAVY:'#fff','left');x+=ww+sp;});g.restore();}
function chrome(t){T('PLANO DE TRÁMITE · ALCALDÍA',72,96,26,'Elite',LBLUE,'left');T('LÁMINA 01',W-72,96,26,'Elite',LBLUE,'right');
  g.fillStyle='rgba(234,244,255,.6)';g.fillRect(60,124,W-120,2);
  g.strokeStyle=INK;g.lineWidth=2;g.strokeRect(60,262,360,64);g.fillStyle=NAVY;g.fillRect(60,262,360,64);g.strokeRect(60,262,360,64);T('NOTICIA EXPLICADA',240,296,40,'Anton',YEL);
  g.fillStyle=INK;g.fillRect(60,340,960,3);
  g.strokeStyle='rgba(234,244,255,.5)';g.lineWidth=2;g.strokeRect(60,1576,960,14);g.fillStyle=LBLUE;g.fillRect(62,1578,956*clamp(t/TL.total),10);
  // dimension ticks along progress
  for(let i=0;i<=10;i++){const x=60+96*i;g.fillStyle='rgba(234,244,255,.6)';g.fillRect(x,1596,2,12);}}
