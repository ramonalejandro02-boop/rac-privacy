// Detailed karting renderer: top view + rear view. Vector, with gradients/shadows. Units ~px at s=1 (kart ~200 long).
const KC={RED:'#E10600',INK:'#0B0B0E',WH:'#F4F5F7'};
function kRR(g,x,y,w,h,r){g.beginPath();g.moveTo(x+r,y);g.arcTo(x+w,y,x+w,y+h,r);g.arcTo(x+w,y+h,x,y+h,r);g.arcTo(x,y+h,x,y,r);g.arcTo(x,y,x+w,y,r);g.closePath();}
// tire seen from above: w across, h along travel. spin: tread phase. lift 0..1 makes it lighter/higher
function kTireTop(g,cx,cy,w,h,spin,lift){g.save();g.translate(cx,cy);
  if(!lift){g.fillStyle='rgba(0,0,0,0.45)';kRR(g,-w/2+3,-h/2+5,w,h,7);g.fill();}
  const gr=g.createLinearGradient(-w/2,0,w/2,0);gr.addColorStop(0,'#0c0c0e');gr.addColorStop(0.25,'#2c2c31');gr.addColorStop(0.5,'#3a3a40');gr.addColorStop(0.75,'#2c2c31');gr.addColorStop(1,'#0c0c0e');
  g.fillStyle=gr;kRR(g,-w/2,-h/2,w,h,8);g.fill();
  g.save();kRR(g,-w/2,-h/2,w,h,8);g.clip();g.strokeStyle='rgba(255,255,255,0.06)';g.lineWidth=2;const ph=((spin||0)%10+10)%10;for(let y=-h/2-10+ph;y<h/2+10;y+=10){g.beginPath();g.moveTo(-w/2,y);g.lineTo(w/2,y);g.stroke();}g.restore();
  g.fillStyle='rgba(255,255,255,0.12)';kRR(g,-w*0.18,-h/2+3,w*0.12,h-6,3);g.fill();
  g.lineWidth=2;g.strokeStyle='#000';kRR(g,-w/2,-h/2,w,h,8);g.stroke();g.restore();}
function tube(g,pts,w,col){g.save();g.lineCap='round';g.lineJoin='round';g.strokeStyle='#111';g.lineWidth=w+3;g.beginPath();pts.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1]));g.stroke();
  g.strokeStyle=col||'#9CA3AF';g.lineWidth=w;g.stroke();g.strokeStyle='rgba(255,255,255,0.55)';g.lineWidth=Math.max(1,w*0.3);g.stroke();g.restore();}
// o: {steer (rad), spin, body, accent, num, liftInner: 0..1 (which side is inner: o.inner = -1 left / 1 right), axleGlow 0..1, ghost}
function kartTop(g,x,y,ang,s,o){o=o||{};const st=o.steer||0,sp=o.spin||0,body=o.body||KC.RED,acc=o.accent||'#111',lift=o.liftInner||0,inner=o.inner||-1;
  g.save();g.translate(x,y);g.rotate(ang+Math.PI/2);g.scale(s,s);
  // soft ground shadow
  g.save();g.filter='blur(10px)';g.fillStyle='rgba(0,0,0,0.55)';kRR(g,-78,-104,164,226,40);g.fill();g.restore();
  // rear tires
  for(const sx of [-1,1]){const l=(sx===inner)?lift:0;g.save();if(l>0){g.translate(sx*-3*l,-6*l);g.scale(1+0.12*l,1+0.12*l);}kTireTop(g,sx*66,62,36,58,sp,l>0.05);g.restore();
    if(l>0.05){g.save();g.globalAlpha=0.35*l;g.filter='blur(6px)';g.fillStyle='#000';kRR(g,sx*66-18+sx*10*l,62-29+14*l,36,58,8);g.fill();g.restore();}}
  // rear axle
  const ag=o.axleGlow||0;if(ag>0){g.save();g.shadowColor=KC.RED;g.shadowBlur=30*ag;tube(g,[[-60,62],[60,62]],10,KC.RED);g.restore();}else tube(g,[[-60,62],[60,62]],8,'#B8BEC8');
  // front tires (steer)
  for(const sx of [-1,1]){g.save();g.translate(sx*58,-66);g.rotate(st);kTireTop(g,0,0,28,46,sp,false);g.restore();}
  // chassis frame
  tube(g,[[-34,-92],[-40,-30],[-42,40],[-36,80]],6);tube(g,[[34,-92],[40,-30],[42,40],[36,80]],6);
  tube(g,[[-40,-66],[40,-66]],5);tube(g,[[-42,20],[42,20]],5);tube(g,[[-46,-66],[-56,-66]],5);tube(g,[[46,-66],[56,-66]],5);
  // floor tray
  g.fillStyle='rgba(60,62,70,0.9)';kRR(g,-30,-60,60,120,10);g.fill();
  // side pods
  for(const sx of [-1,1]){g.save();g.scale(sx,1);const gr=g.createLinearGradient(48,0,82,0);gr.addColorStop(0,body);gr.addColorStop(1,shade(body,0.6));g.fillStyle=gr;
    g.beginPath();g.moveTo(48,-30);g.lineTo(76,-24);g.quadraticCurveTo(84,8,78,34);g.lineTo(50,40);g.closePath();g.fill();g.lineWidth=2.5;g.strokeStyle='#000';g.stroke();
    g.fillStyle=acc;g.beginPath();g.moveTo(56,-18);g.lineTo(74,-14);g.lineTo(72,-4);g.lineTo(55,-8);g.closePath();g.fill();g.restore();}
  // front nose fairing + bumper
  tube(g,[[-60,-108],[60,-108]],5,'#7d838d');
  const ng=g.createLinearGradient(0,-130,0,-82);ng.addColorStop(0,shade(body,1.15));ng.addColorStop(1,shade(body,0.7));g.fillStyle=ng;
  g.beginPath();g.moveTo(-62,-104);g.quadraticCurveTo(-60,-128,-30,-128);g.lineTo(30,-128);g.quadraticCurveTo(60,-128,62,-104);g.lineTo(40,-86);g.lineTo(-40,-86);g.closePath();g.fill();g.lineWidth=2.5;g.strokeStyle='#000';g.stroke();
  g.fillStyle=acc;g.beginPath();g.moveTo(-50,-104);g.lineTo(-20,-122);g.lineTo(-10,-122);g.lineTo(-40,-100);g.closePath();g.fill();g.beginPath();g.moveTo(50,-104);g.lineTo(20,-122);g.lineTo(10,-122);g.lineTo(40,-100);g.closePath();g.fill();
  // front panel (number)
  g.fillStyle=shade(body,0.85);g.beginPath();g.moveTo(-20,-86);g.lineTo(20,-86);g.lineTo(16,-44);g.lineTo(-16,-44);g.closePath();g.fill();g.stroke();
  if(o.num){g.fillStyle='#FFD400';kRR(g,-13,-80,26,24,4);g.fill();g.fillStyle='#000';g.font='italic 900 20px BC, sans-serif';g.textAlign='center';g.textBaseline='middle';g.fillText(o.num,0,-67);}
  // steering column + wheel
  tube(g,[[0,-44],[0,-24]],4,'#555');
  // engine (right side) + exhaust
  g.fillStyle='#4a4d55';kRR(g,40,22,30,34,5);g.fill();g.strokeStyle='#000';g.lineWidth=2;g.stroke();g.strokeStyle='rgba(255,255,255,0.2)';for(let i=0;i<5;i++){g.beginPath();g.moveTo(42,26+i*6);g.lineTo(68,26+i*6);g.stroke();}
  tube(g,[[56,56],[60,84],[40,98],[10,100]],7,'#8b8f98');
  // rear bumper
  const rb=g.createLinearGradient(0,92,0,116);rb.addColorStop(0,shade(body,1.1));rb.addColorStop(1,shade(body,0.6));g.fillStyle=rb;kRR(g,-82,96,164,20,8);g.fill();g.lineWidth=2.5;g.strokeStyle='#000';g.stroke();
  // seat
  g.fillStyle='#16171b';g.beginPath();g.ellipse(-4,16,26,34,0,0,7);g.fill();
  // driver: shoulders, arms, gloves, helmet
  g.fillStyle='#2347C6';g.beginPath();g.ellipse(-4,8,30,18,0,0,7);g.fill();g.strokeStyle='#000';g.lineWidth=2;g.stroke();
  for(const sx of [-1,1]){tube(g,[[sx*24-4,4],[sx*20,-14],[sx*12,-30]],9,'#2347C6');g.fillStyle=KC.RED;g.beginPath();g.arc(sx*12,-31,6,0,7);g.fill();}
  g.strokeStyle='#111';g.lineWidth=5;g.beginPath();g.ellipse(0,-30,16,6,0,0,7);g.stroke();
  const hg=g.createRadialGradient(-6,-6,2,-2,0,22);hg.addColorStop(0,'#ffffff');hg.addColorStop(1,'#c9ccd3');g.fillStyle=hg;g.beginPath();g.arc(-3,-2,17,0,7);g.fill();g.strokeStyle='#000';g.lineWidth=2;g.stroke();
  g.fillStyle=KC.RED;g.fillRect(-7,-19,8,34);g.fillStyle='#ffb000';g.beginPath();g.arc(-3,-2,17,-2.3,-0.85);g.lineTo(-3,-2);g.closePath();g.globalAlpha=0.9;g.fill();g.globalAlpha=1;
  g.restore();}
function shade(hex,f){const n=parseInt(hex.slice(1),16);let r=(n>>16)&255,gg=(n>>8)&255,b=n&255;r=Math.min(255,r*f);gg=Math.min(255,gg*f);b=Math.min(255,b*f);return `rgb(${r|0},${gg|0},${b|0})`;}
// rear view: origin = ground centre. tilt: lift of left(inner) wheel in px. twist: chassis flex visual 0..1
function kartRear(g,x,y,s,o){o=o||{};const lift=o.lift||0,body=o.body||KC.RED;
  g.save();g.translate(x,y);g.scale(s,s);
  // ground shadow
  g.save();g.filter='blur(8px)';g.fillStyle='rgba(0,0,0,0.6)';g.beginPath();g.ellipse(0,6,330,22,0,0,7);g.fill();g.restore();
  // pivot about outer (right) wheel contact
  const ang=Math.atan2(lift,520);g.translate(260,0);g.rotate(-ang);g.translate(-260,0);
  const tire=(cx)=>{const gr=g.createLinearGradient(cx-55,0,cx+55,0);gr.addColorStop(0,'#0b0b0d');gr.addColorStop(0.5,'#34343a');gr.addColorStop(1,'#0b0b0d');g.fillStyle=gr;kRR(g,cx-55,-150,110,150,22);g.fill();g.lineWidth=4;g.strokeStyle='#000';g.stroke();
    g.fillStyle='#C9CDD5';kRR(g,cx-30,-102,60,54,10);g.fill();g.stroke();g.fillStyle='rgba(255,255,255,0.15)';kRR(g,cx-48,-146,20,140,8);g.fill();};
  tire(-260);tire(260);
  // axle + bearings
  const ag=o.axleGlow||0;g.save();if(ag>0){g.shadowColor=KC.RED;g.shadowBlur=30*ag;}g.fillStyle=ag>0?KC.RED:'#B8BEC8';kRR(g,-250,-84,500,14,6);g.fill();g.restore();
  for(const bx of [-150,150]){g.fillStyle='#555a63';kRR(g,bx-20,-100,40,44,6);g.fill();g.strokeStyle='#000';g.lineWidth=3;g.stroke();}
  // chassis rails (flex: bend downward in the middle)
  const fx=o.flex||0;g.strokeStyle='#9CA3AF';g.lineWidth=12;g.lineCap='round';g.beginPath();g.moveTo(-200,-60);g.quadraticCurveTo(0,-60+fx*28,200,-60);g.stroke();g.strokeStyle='rgba(255,255,255,0.6)';g.lineWidth=3;g.stroke();
  // engine (right) + exhaust
  g.fillStyle='#4a4d55';kRR(g,90,-210,90,110,10);g.fill();g.strokeStyle='#000';g.lineWidth=3;g.stroke();for(let i=0;i<6;i++){g.fillStyle='#6a6e78';g.fillRect(96,-202+i*16,78,6);}
  g.strokeStyle='#8b8f98';g.lineWidth=16;g.beginPath();g.moveTo(170,-120);g.quadraticCurveTo(230,-120,220,-40);g.stroke();
  // seat
  g.fillStyle='#1a1b20';kRR(g,-70,-230,120,150,30);g.fill();
  // driver back
  g.fillStyle='#2347C6';g.beginPath();g.moveTo(-90,-200);g.quadraticCurveTo(-10,-250,70,-200);g.lineTo(60,-120);g.lineTo(-80,-120);g.closePath();g.fill();g.strokeStyle='#000';g.lineWidth=3;g.stroke();
  g.fillStyle=KC.RED;g.fillRect(-82,-170,152,14);
  const hg=g.createRadialGradient(-30,-336,5,-10,-316,70);hg.addColorStop(0,'#fff');hg.addColorStop(1,'#c4c7cf');g.fillStyle=hg;g.fillStyle='#111';g.fillRect(-28,-270,36,30);g.fillStyle=hg;g.beginPath();g.ellipse(-10,-318,58,62,0,0,7);g.fill();g.stroke();
  g.save();g.beginPath();g.ellipse(-10,-318,58,62,0,0,7);g.clip();g.fillStyle=KC.RED;g.fillRect(-18,-390,16,140);g.restore();g.fillStyle='#000';g.font='italic 900 34px BC, sans-serif';g.textAlign='center';g.fillText('2',-10,-296);
  // rear bumper
  const rb=g.createLinearGradient(0,-70,0,-20);rb.addColorStop(0,shade(body,1.1));rb.addColorStop(1,shade(body,0.55));g.fillStyle=rb;kRR(g,-200,-62,400,40,14);g.fill();g.strokeStyle='#000';g.lineWidth=3;g.stroke();
  g.fillStyle='#fff';g.font='italic 900 26px BC, sans-serif';g.fillText('MAURO OSORTO',0,-34);
  g.restore();}
