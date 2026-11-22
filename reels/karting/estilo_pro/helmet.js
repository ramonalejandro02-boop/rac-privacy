// "MO-2" — Maurito's pro helmet mascot. Esports / F1-emblem style: glossy white shell, red racing stripe,
// black chin bar, dark visor with expressive eyes. Draws centred at the origin, ~420 px wide at scale 1.
const HM = {RED:'#E10600', RED2:'#8C0400', INK:'#0B0B0E', WHITE:'#F7F7F9'};
function hmShell(g){g.beginPath();g.moveTo(-178,60);g.bezierCurveTo(-200,-80,-120,-196,10,-198);g.bezierCurveTo(140,-200,205,-110,200,10);g.bezierCurveTo(198,70,182,118,150,150);g.lineTo(-120,150);g.bezierCurveTo(-160,130,-176,100,-178,60);g.closePath();}
function hmVisor(g){g.beginPath();g.moveTo(-138,-28);g.bezierCurveTo(-120,-70,-20,-78,120,-62);g.bezierCurveTo(176,-56,196,-20,192,22);g.bezierCurveTo(188,62,160,76,110,76);g.lineTo(-90,74);g.bezierCurveTo(-140,72,-152,20,-138,-28);g.closePath();}
// o: {blink 0..1, mood 'focus'|'happy'|'wow'|'angry', look {x,y}, glow 0..1, t}
function drawHelmet(g,o){o=o||{};const blink=o.blink||0,mood=o.mood||'focus',lx=(o.look&&o.look.x)||0,ly=(o.look&&o.look.y)||0,glow=o.glow==null?1:o.glow;
  g.save();
  // red back-glow
  if(glow>0){const rg=g.createRadialGradient(0,-10,60,0,-10,320);rg.addColorStop(0,`rgba(225,6,0,${0.55*glow})`);rg.addColorStop(1,'rgba(225,6,0,0)');g.fillStyle=rg;g.fillRect(-340,-340,680,680);}
  // drop shadow
  g.save();g.translate(14,18);hmShell(g);g.fillStyle='rgba(0,0,0,0.55)';g.fill();g.restore();
  // shell base
  hmShell(g);const sg=g.createLinearGradient(-180,-200,180,150);sg.addColorStop(0,'#FFFFFF');sg.addColorStop(0.55,'#E9EBF0');sg.addColorStop(1,'#B9BCC6');g.fillStyle=sg;g.fill();
  g.save();hmShell(g);g.clip();
  // red racing stripe sweeping over the top
  g.beginPath();g.moveTo(-60,-220);g.bezierCurveTo(40,-200,120,-120,230,-60);g.lineTo(230,-10);g.bezierCurveTo(130,-70,40,-150,-110,-190);g.closePath();
  const rg2=g.createLinearGradient(-60,-220,230,-10);rg2.addColorStop(0,HM.RED);rg2.addColorStop(1,HM.RED2);g.fillStyle=rg2;g.fill();
  g.beginPath();g.moveTo(-130,-176);g.bezierCurveTo(20,-140,110,-70,230,0);g.lineTo(230,14);g.bezierCurveTo(110,-56,10,-126,-140,-160);g.closePath();g.fillStyle=HM.INK;g.fill();
  // MAURO on the stripe
  g.save();g.translate(70,-142);g.rotate(0.5);g.font='italic 900 30px "BC"';g.fillStyle='#fff';g.textAlign='center';g.textBaseline='middle';g.fillText('MAURO',0,0);g.restore();
  // chin bar (black) with red vents
  g.beginPath();g.moveTo(-180,40);g.bezierCurveTo(-150,90,-60,110,60,104);g.bezierCurveTo(140,100,190,80,210,40);g.lineTo(210,200);g.lineTo(-200,200);g.closePath();
  const cg=g.createLinearGradient(0,60,0,160);cg.addColorStop(0,'#26262C');cg.addColorStop(1,'#0B0B0E');g.fillStyle=cg;g.fill();
  g.fillStyle=HM.RED;for(let i=0;i<3;i++){g.beginPath();g.moveTo(-10+i*34,118);g.lineTo(14+i*34,118);g.lineTo(2+i*34,140);g.lineTo(-22+i*34,140);g.closePath();g.fill();}
  // gloss
  g.globalAlpha=0.55;g.beginPath();g.ellipse(-60,-150,90,26,-0.35,0,7);g.fillStyle='#fff';g.fill();g.globalAlpha=1;
  g.restore();
  hmShell(g);g.lineWidth=8;g.strokeStyle=HM.INK;g.stroke();
  // visor
  hmVisor(g);const vg=g.createLinearGradient(0,-70,0,76);vg.addColorStop(0,'#1A1A20');vg.addColorStop(1,'#050506');g.fillStyle=vg;g.fill();g.lineWidth=8;g.strokeStyle=HM.INK;g.stroke();
  g.save();hmVisor(g);g.clip();
  // eyes
  const eye=(cx,cy,flip)=>{g.save();g.translate(cx,cy);g.scale(flip,1);
    const sy=Math.max(0.08,1-blink);g.scale(1,sy);
    g.beginPath();
    if(mood==='happy'){g.moveTo(-34,8);g.quadraticCurveTo(0,-30,34,8);g.quadraticCurveTo(0,-8,-34,8);}
    else if(mood==='wow'){g.ellipse(0,0,28,34,0,0,7);}
    else if(mood==='angry'){g.moveTo(-36,-12);g.lineTo(34,6);g.quadraticCurveTo(30,30,0,30);g.quadraticCurveTo(-34,28,-36,-12);}
    else {g.moveTo(-36,-4);g.lineTo(34,-14);g.quadraticCurveTo(36,26,2,28);g.quadraticCurveTo(-34,26,-36,-4);}
    g.closePath();g.shadowColor='rgba(255,40,30,0.9)';g.shadowBlur=24;g.fillStyle='#FFFFFF';g.fill();g.shadowBlur=0;
    if(mood!=='happy'){g.beginPath();g.arc(lx*10*flip+4,ly*8+8,13,0,7);g.fillStyle=HM.RED;g.fill();g.beginPath();g.arc(lx*10*flip+4,ly*8+8,6,0,7);g.fillStyle=HM.INK;g.fill();g.beginPath();g.arc(lx*10*flip+9,ly*8+3,4,0,7);g.fillStyle='#fff';g.fill();}
    g.restore();};
  eye(-30,10,1);eye(96,6,-1);
  // visor reflection
  g.globalAlpha=0.28;g.beginPath();g.moveTo(-120,-60);g.lineTo(40,-70);g.lineTo(-10,-20);g.lineTo(-140,-10);g.closePath();g.fillStyle='#fff';g.fill();g.globalAlpha=1;
  g.restore();
  // number on the chin bar
  g.save();g.translate(-118,112);g.rotate(-0.12);g.font='italic 900 74px "BC"';g.textAlign='center';g.textBaseline='middle';g.lineWidth=10;g.strokeStyle=HM.RED;g.strokeText('2',0,0);g.fillStyle='#fff';g.fillText('2',0,0);g.restore();
  // spoiler
  g.beginPath();g.moveTo(-150,-130);g.lineTo(-215,-150);g.lineTo(-205,-118);g.lineTo(-160,-104);g.closePath();g.fillStyle=HM.INK;g.fill();
  g.restore();
}
