// Maurito mascot — flat cartoon, thick outlines. All functions draw centered at current origin.
const OL='#16121c', SKIN='#f4c39a', SKIN2='#e5a77c', HELM='#ffffff', BLUE='#1f3fc4', BLUE2='#16309a', MRED='#e0262b', MRED2='#b51a1f', BROWN='#5a341a', HAIR='#3b2414';
function _rr(g,x,y,w,h,r){g.beginPath();g.moveTo(x+r,y);g.arcTo(x+w,y,x+w,y+h,r);g.arcTo(x+w,y+h,x,y+h,r);g.arcTo(x,y+h,x,y,r);g.arcTo(x,y,x+w,y,r);g.closePath();}
function _fs(g,fill,lw){g.fillStyle=fill;g.fill();g.lineWidth=lw||7;g.strokeStyle=OL;g.lineJoin='round';g.stroke();}
function curvedText(g,txt,r,centerAng,font,fill,spacing){g.save();g.font=font;g.textAlign='center';g.textBaseline='middle';
  const ws=[...txt].map(c=>g.measureText(c).width*(spacing||1));const tot=ws.reduce((a,b)=>a+b,0);let a=centerAng-tot/r/2;
  [...txt].forEach((c,i)=>{const aa=a+ws[i]/r/2;g.save();g.rotate(aa+Math.PI/2);g.translate(0,-r);
    g.lineWidth=7;g.strokeStyle=OL;g.strokeText(c,0,0);g.fillStyle=fill;g.fillText(c,0,0);g.restore();a+=ws[i]/r;});g.restore();}
// o: {talk:0..1, blink:0..1, look:{x,y}, mood:'happy'|'worried'|'wow'}
function mauritoHead(g,o){o=o||{};const talk=o.talk||0,blink=o.blink||0,lx=(o.look&&o.look.x)||0,ly=(o.look&&o.look.y)||0,mood=o.mood||'happy';
  g.save();
  // helmet shell
  g.beginPath();g.ellipse(0,-8,112,106,0,0,Math.PI*2);
  const hg=g.createRadialGradient(-40,-60,10,0,-8,120);hg.addColorStop(0,'#ffffff');hg.addColorStop(1,'#dfe5ee');_fs(g,hg,8);
  // bottom rim of helmet (dark liner around face)
  _rr(g,-92,-40,184,156,66);g.fillStyle='#24242c';g.fill();
  // face
  _rr(g,-80,-30,160,138,58);
  const fg=g.createLinearGradient(0,-24,0,98);fg.addColorStop(0,SKIN);fg.addColorStop(1,SKIN2);_fs(g,fg,5);
  // hair fringe
  g.beginPath();g.moveTo(-74,-4);g.quadraticCurveTo(-50,-36,-14,-28);g.quadraticCurveTo(10,-42,36,-26);g.quadraticCurveTo(62,-34,74,-2);g.quadraticCurveTo(48,-16,22,-10);g.quadraticCurveTo(0,-20,-24,-8);g.quadraticCurveTo(-50,-16,-74,-4);g.closePath();_fs(g,HAIR,4);
  // visor edge line + stripes
  g.beginPath();g.ellipse(0,-8,112,106,0,Math.PI*1.08,Math.PI*1.92);g.lineWidth=0;
  g.save();g.beginPath();g.ellipse(0,-8,112,106,0,0,Math.PI*2);g.clip();
  g.fillStyle=BLUE;g.fillRect(-120,-48,240,10);
  g.fillStyle='#22a04a';g.beginPath();g.moveTo(80,40);g.lineTo(120,10);g.lineTo(120,22);g.lineTo(84,52);g.fill();
  g.fillStyle='#f6c400';g.beginPath();g.moveTo(84,52);g.lineTo(120,22);g.lineTo(120,34);g.lineTo(88,64);g.fill();
  g.fillStyle=BLUE;g.beginPath();g.moveTo(40,98);g.lineTo(110,60);g.lineTo(108,72);g.lineTo(46,108);g.fill();
  g.restore();
  g.beginPath();g.ellipse(0,-8,112,106,0,0,Math.PI*2);g.lineWidth=8;g.strokeStyle=OL;g.stroke();
  // MAURO lettering
  curvedText(g,'MAURO',82,-Math.PI/2,'900 38px "Inter Display",Inter,sans-serif',BLUE,1.05);
  // number 2 on the side
  g.save();g.translate(95,18);g.rotate(0.12);g.font='italic 900 54px "Inter Display",Inter';g.textAlign='center';g.textBaseline='middle';g.lineWidth=8;g.strokeStyle=OL;g.strokeText('2',0,0);g.fillStyle=MRED;g.fillText('2',0,0);g.restore();
  // eyebrows
  g.strokeStyle=HAIR;g.lineWidth=7;g.lineCap='round';
  const brow=mood==='worried'?[[-48,6,-18,0],[18,0,48,6]]:mood==='wow'?[[-48,-4,-18,-8],[18,-8,48,-4]]:[[-56,2,-20,-6],[20,-6,56,2]];
  if(mood==='worried'){g.beginPath();g.moveTo(-50,8);g.lineTo(-18,-2);g.stroke();g.beginPath();g.moveTo(18,-2);g.lineTo(50,8);g.stroke();}
  else brow.forEach(b=>{g.beginPath();g.moveTo(b[0],b[1]);g.quadraticCurveTo((b[0]+b[2])/2,b[1]-8,b[2],b[3]);g.stroke();});
  // eyes
  for(const ex of [-34,34]){g.save();g.translate(ex,32);g.scale(1.18,1.18);const sy=1-0.9*blink;g.scale(1,Math.max(0.08,sy));
    g.beginPath();g.ellipse(0,0,19,23,0,0,Math.PI*2);_fs(g,'#fff',4);
    g.beginPath();g.arc(lx*5,ly*5+2,14,0,7);g.fillStyle='#7a4518';g.fill();
    g.beginPath();g.arc(lx*5,ly*5+3,8,0,7);g.fillStyle='#1b0f08';g.fill();
    g.beginPath();g.arc(lx*5+5,ly*5-4,4.5,0,7);g.fillStyle='#fff';g.fill();g.beginPath();g.arc(lx*5-4,ly*5+7,2,0,7);g.fill();
    g.restore();}
  // nose
  g.strokeStyle='#b8744f';g.lineWidth=4;g.beginPath();g.moveTo(-2,52);g.quadraticCurveTo(4,58,-2,62);g.stroke();
  // cheeks
  g.fillStyle='rgba(255,120,120,0.35)';g.beginPath();g.ellipse(-46,62,12,7,0,0,7);g.fill();g.beginPath();g.ellipse(46,62,12,7,0,0,7);g.fill();
  // mouth
  const mo=mood==='wow'?0.9:talk;
  if(mood==='worried'&&talk<0.2){g.strokeStyle=OL;g.lineWidth=5;g.beginPath();g.moveTo(-18,82);g.quadraticCurveTo(0,72,18,82);g.stroke();}
  else{g.beginPath();g.moveTo(-32,70);g.quadraticCurveTo(0,80+mo*18,32,70);g.quadraticCurveTo(0,92+mo*34,-32,70);g.closePath();_fs(g,'#8c1d24',4);
    g.save();g.clip();g.fillStyle='#fff';g.fillRect(-32,68,64,8+mo*3);g.fillStyle='#e8656e';g.beginPath();g.ellipse(0,88+mo*26,14,8,0,0,7);g.fill();g.restore();}
  g.restore();
}
// upper body front (shoulders + chest) drawn below head; arms optional handled by caller
function mauritoTorso(g){
  g.save();
  // neck brace
  _rr(g,-56,92,112,30,14);_fs(g,'#1e1e24',6);
  // torso
  g.beginPath();g.moveTo(-92,130);g.quadraticCurveTo(-96,112,-60,112);g.lineTo(60,112);g.quadraticCurveTo(96,112,92,130);g.lineTo(86,250);g.lineTo(-86,250);g.closePath();
  const tg=g.createLinearGradient(0,112,0,250);tg.addColorStop(0,BLUE);tg.addColorStop(1,BLUE2);_fs(g,tg,7);
  // red shoulder panels
  g.save();g.clip();g.fillStyle=MRED;g.beginPath();g.moveTo(-100,110);g.lineTo(-30,110);g.lineTo(-70,180);g.lineTo(-100,190);g.fill();g.beginPath();g.moveTo(100,110);g.lineTo(30,110);g.lineTo(70,180);g.lineTo(100,190);g.fill();
  g.fillStyle=MRED;g.fillRect(-100,222,200,30);g.restore();
  g.beginPath();g.moveTo(-92,130);g.quadraticCurveTo(-96,112,-60,112);g.lineTo(60,112);g.quadraticCurveTo(96,112,92,130);g.lineTo(86,250);g.lineTo(-86,250);g.closePath();g.lineWidth=7;g.strokeStyle=OL;g.stroke();
  // harness straps
  g.fillStyle='#d9dde5';_rr(g,-54,112,18,110,6);_fs(g,'#e9ecf2',4);_rr(g,36,112,18,110,6);_fs(g,'#e9ecf2',4);
  // MO logo
  g.font='italic 900 46px "Inter Display",Inter';g.textAlign='center';g.textBaseline='middle';g.lineWidth=7;g.strokeStyle=OL;g.strokeText('MO',0,170);g.fillStyle='#fff';g.fillText('MO',0,170);
  // belt buckle
  _rr(g,-26,224,52,26,6);_fs(g,MRED,5);g.font='900 22px "Inter Display",Inter';g.fillStyle='#fff';g.fillText('2',0,238);
  g.restore();
}
function glove(g,x,y,r,fist){g.save();g.translate(x,y);g.beginPath();g.ellipse(0,0,r*1.05,r,0,0,7);_fs(g,MRED,6);
  g.strokeStyle=MRED2;g.lineWidth=3;for(let i=-1;i<=1;i++){g.beginPath();g.moveTo(-r*0.6,i*r*0.38);g.lineTo(r*0.3,i*r*0.38);g.stroke();}g.restore();}
function arm(g,x1,y1,x2,y2,w){g.save();g.lineCap='round';g.strokeStyle=OL;g.lineWidth=w+14;g.beginPath();g.moveTo(x1,y1);g.lineTo(x2,y2);g.stroke();
  g.strokeStyle=BLUE;g.lineWidth=w;g.stroke();g.strokeStyle=MRED;g.lineWidth=w*0.35;g.beginPath();g.moveTo(x1,y1);g.lineTo((x1+x2)/2,(y1+y2)/2);g.stroke();g.restore();}
// full standing pose (celebration without trophy): fistUp 0..1 raises right arm
function mauritoStanding(g,o){o=o||{};const up=o.fistUp==null?1:o.fistUp;
  g.save();
  // legs
  for(const sx of [-1,1]){g.save();g.translate(sx*40,250);_rr(g,-30,-6,60,120,20);_fs(g,BLUE,7);g.fillStyle=MRED;g.fillRect(-28+ (sx>0?36:0),0,14,110);_rr(g,-30,-6,60,120,20);g.lineWidth=7;g.strokeStyle=OL;g.stroke();
    _rr(g,-36,104,74,40,16);_fs(g,MRED,7);_rr(g,-36,128,74,16,8);_fs(g,'#fff',5);g.font='italic 900 20px "Inter Display",Inter';g.fillStyle='#fff';g.textAlign='center';g.fillText('MO',0,122);g.restore();}
  // arms
  const ax=-110+0*up, ayUp=lerpM(170,-60,up), axUp=lerpM(-120,-150,up);
  arm(g,-80,140,axUp,ayUp,40); glove(g,axUp,ayUp-10*up,30,true);
  arm(g,80,140,120,250,40); glove(g,124,262,28,true);
  mauritoTorso(g);
  mauritoHead(g,o);
  g.restore();
}
function lerpM(a,b,f){return a+(b-a)*f;}
// waving pose for intro (upper body only, behind a kart)
function mauritoWave(g,o,wave){
  g.save();
  const wx=150+Math.sin(wave)*16, wy=40+Math.cos(wave)*6;
  arm(g,80,140,wx,wy+60,38);g.save();g.translate(wx,wy+30);g.rotate(Math.sin(wave)*0.3);
  // open hand
  g.beginPath();g.ellipse(0,0,30,34,0,0,7);_fs(g,MRED,6);for(let i=0;i<4;i++){g.save();g.rotate(-0.6+i*0.4);_rr(g,-7,-58,14,30,7);_fs(g,MRED,5);g.restore();}g.restore();
  mauritoTorso(g);mauritoHead(g,o);g.restore();
}
