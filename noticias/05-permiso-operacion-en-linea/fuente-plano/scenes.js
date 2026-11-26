
function ambient(t){}
function walker(x,y,s,col,t,ph=0,tired=0){g.save();g.translate(x,y);g.scale(s,s);const bob=Math.abs(Math.sin(t*3+ph))*4;g.translate(0,-bob+tired*6);g.rotate(tired*.12);
  g.fillStyle=col;g.beginPath();g.arc(0,-62,15,0,7);g.fill();rr(-15,-46,30,46,8);g.fill();g.fillRect(-12,0,9,30);g.fillRect(3,0,9,30);g.strokeStyle=INK;g.lineWidth=3;g.beginPath();g.arc(0,-62,15,0,7);g.stroke();g.restore();}
function building(x,y,s,label_='ALCALDÍA'){g.save();g.translate(x,y);g.scale(s,s);shadowed(()=>{g.fillStyle=CREAM;g.fillRect(-120,-200,240,200);},10,.3);g.strokeStyle=INK;g.lineWidth=5;g.strokeRect(-120,-200,240,200);
  g.fillStyle=BLUE;g.fillRect(-120,-240,240,40);g.strokeRect(-120,-240,240,40);T(label_,0,-218,30,'Anton','#fff');
  g.fillStyle='#8db8e3';for(let r=0;r<3;r++)for(let c=0;c<4;c++){g.fillRect(-100+c*52,-185+r*50,34,32);g.strokeRect(-100+c*52,-185+r*50,34,32);}g.fillStyle=INK;g.fillRect(-25,-45,50,45);g.restore();}
function clock(cx,cy,r,ang,col=INK){g.save();g.translate(cx,cy);shadowed(()=>{g.fillStyle=PANEL;g.beginPath();g.arc(0,0,r,0,7);g.fill();},10,.3);g.strokeStyle=col;g.lineWidth=r*.07;g.beginPath();g.arc(0,0,r,0,7);g.stroke();
  for(let i=0;i<12;i++){const a=i/12*Math.PI*2;g.beginPath();g.moveTo(Math.cos(a)*r*.82,Math.sin(a)*r*.82);g.lineTo(Math.cos(a)*r*.92,Math.sin(a)*r*.92);g.stroke();}
  g.lineCap='round';g.lineWidth=r*.07;g.beginPath();g.moveTo(0,0);g.lineTo(Math.cos(ang/12-Math.PI/2)*r*.5,Math.sin(ang/12-Math.PI/2)*r*.5);g.stroke();
  g.strokeStyle=RED;g.lineWidth=r*.04;g.beginPath();g.moveTo(0,0);g.lineTo(Math.cos(ang-Math.PI/2)*r*.78,Math.sin(ang-Math.PI/2)*r*.78);g.stroke();g.fillStyle=INK;g.beginPath();g.arc(0,0,r*.06,0,7);g.fill();g.restore();}
function phone(cx,cy,s,fn){g.save();g.translate(cx,cy);g.scale(s,s);shadowed(()=>{g.fillStyle=NAVY;rr(-170,-330,340,660,44);g.fill();g.strokeStyle=INK;g.lineWidth=4;rr(-170,-330,340,660,44);g.stroke();},16,.35);g.fillStyle=PANEL;rr(-150,-300,300,600,30);g.fill();
  g.fillStyle=NAVY;rr(-40,-290,80,16,8);g.fill();g.save();rr(-150,-300,300,600,30);g.clip();fn();g.restore();g.restore();}
function cross(x,y,s,p){if(p<=0)return;g.save();g.translate(x,y);g.strokeStyle=RED;g.lineWidth=s*.18;g.lineCap='round';const a=clamp(p*2),b=clamp(p*2-1);
  g.beginPath();g.moveTo(-s/2,-s/2);g.lineTo(lerp(-s/2,s/2,a),lerp(-s/2,s/2,a));g.stroke();if(b>0){g.beginPath();g.moveTo(s/2,-s/2);g.lineTo(lerp(s/2,-s/2,b),lerp(-s/2,s/2,b));g.stroke();}g.restore();}
function sig(x,y,p,s=1,col=BLUE,seed=0){if(p<=0)return;g.save();g.translate(x,y);g.scale(s,s);g.strokeStyle=col;g.lineWidth=5;g.lineCap='round';g.lineJoin='round';g.beginPath();
  const N=Math.floor(120*clamp(p));for(let i=0;i<=N;i++){const u=i/120;const xx=u*300+Math.sin(u*(36+seed*7))*18;const yy=Math.sin(u*(22+seed*5))*22*Math.exp(-u*1.5)-u*10+Math.cos(u*13+seed)*8;i?g.lineTo(xx,yy):g.moveTo(xx,yy);}g.stroke();g.restore();}
const QCOL=[BLUE,RED,GREEN,GOLD,'#7a5bbf',AMB];
function queue(t,y,n,dx,startX,tired=0,crossed=0){for(let i=0;i<n;i++){const x=startX+i*dx;if(x<-60||x>W+60)continue;walker(x,y,1.3,QCOL[i%6],t,i*1.3,tired);}}

function sc1(t){
  headline('¿TE ACORDÁS?',450,130,RED,k(t,.05,.4));
  building(170,1040,1.1);
  const cp=back(k(t,EV.enero,.4));if(cp>0){g.save();g.translate(850,720);g.rotate(.1);g.scale(cp,cp);shadowed(()=>{g.fillStyle=PANEL;g.fillRect(-120,-110,240,200);},12,.3);g.fillStyle=RED;g.fillRect(-120,-110,240,50);T('ENERO',0,20,84,'Anton',INK);
    g.fillStyle=INK;for(let i=-90;i<=90;i+=45){g.beginPath();g.arc(i,-110,7,0,7);g.fill();}g.restore();}
  const qp=eio(k(t,EV.filas-.3,2.5));const n=Math.round(lerp(2,16,qp));const shift=((t*30)%80);
  queue(t,1035,n,80,300-0,0);
  label('PERMISO DE OPERACIÓN',W/2+120,1180,k(t,EV.permiso,.35),INK,YEL,48,-.02);
}
function sc2(t){
  const ang=(t-EV.S[1])*9;clock(W/2,700,220,ang);
  const h=Math.min(17,8+Math.floor((t-EV.S[1])*1.6));
  const q=back(k(t,EV.S[1]+.05,.4));if(q>0){g.save();g.translate(W/2,1000);g.scale(q,q);num((h<10?'0':'')+h+':00',0,0,110,INK);g.restore();}
  stamp('1 DÍA PERDIDO',W/2,450,74,-.06,t,EV.perdido,RED);
  // tramitador with hand out
  const tp=k(t,EV.trami-.4,.5);if(tp>0){const x=lerp(W+200,W/2,back(tp));g.save();g.translate(x-W/2,0);walker(W/2-60,1270,1.6,INK,t,0);
    g.fillStyle=INK;g.fillRect(W/2-60-30,1270-130,60,14);g.fillRect(W/2-60-20,1270-160,40,32);
    coin(W/2+40,1180+Math.sin(t*6)*10,26,t*6);coin(W/2+90,1220+Math.sin(t*6+1)*10,22,t*6+1);T('TRAMITADOR',W/2+60,1320,40,'Anton',RED,'left');g.restore();}
  label('A VECES MÁS',W/2+250,1080,k(t,EV.veces,.35),RED,'#fff',44,.04);
}
function sc3(t){
  queue(t,1000,14,80,-20,1);
  const p=k(t,EV.acaba-.1,.2);if(p>0){g.save();g.fillStyle=`rgba(15,76,129,${.55*p})`;g.fillRect(0,360,W,1000);g.restore();}
  stamp('SE ACABA',W/2,760,170,-.1,t,EV.acaba,RED);
}
function sc4(t){
  headline('PERMISO 2027',450,100,INK,k(t,EV.y27-.2,.4));
  const pp=k(t,EV.S[3]+.1,.5);if(pp>0){const y=lerp(1700,900,back(pp));const tap=k(t,EV.linea,.25);const done=k(t,EV.linea+.4,.4);
    phone(W/2,y,1.05,()=>{g.fillStyle=BLUE;g.fillRect(-150,-300,300,110);T('ALCALDÍA',0,-230,34,'Anton','#fff');
      T('Permiso de operación',0,-130,24,'Arch',INK);T('2027',0,-80,60,'Anton',INK);
      for(let i=0;i<3;i++){g.fillStyle='rgba(234,244,255,.18)';rr(-120,-20+i*60,240,40,10);g.fill();}
      const bs=1-.08*Math.sin(clamp(tap)*Math.PI);g.save();g.translate(0,220);g.scale(bs,bs);g.fillStyle=done>0?GREEN:RED;rr(-120,-40,240,80,40);g.fill();T(done>0?'¡LISTO!':'RENOVAR',0,4,40,'Anton','#fff');g.restore();
      if(done>0){g.save();g.globalAlpha=done;check(0,120,90,done,GREEN);g.restore();}});
    if(t>EV.linea-.4&&t<EV.linea+.6){const ht=k(t,EV.linea-.4,.4);hand(W/2+40,y+330+lerp(200,0,ease(ht)),tap>0&&tap<1?1:0);}
    confetti(t,EV.linea+.4,W/2,y+150,50);}
  label('EN LÍNEA',W/2-300,700,k(t,EV.linea,.35),GREEN,'#fff',64,-.06);
  label('DESDE TU CELULAR',W/2+250,1340,k(t,EV.cel,.35),INK,YEL,48,.03);
}
function sc5(t){
  label('DECLARACIONES: TAMBIÉN EN LÍNEA',W/2,450,k(t,EV.decl,.35),GREEN,'#fff',56,-.02);
  const items=[['IR AL CENTRO',EV.x1,'build'],['HACER FILAS',EV.x2,'queue'],['TRAMITADOR',EV.x3,'tram']];
  items.forEach(([s,at,ic],i)=>{const y=680+i*240;const a=k(t,at-.5,.4);if(a<=0)return;g.save();g.translate((1-back(a))*-300,0);
    shadowed(()=>{g.fillStyle=CREAM;g.fillRect(90,y-95,900,190);},10,.3);
    g.save();g.translate(220,y);if(ic==='build')building(0,70,.55);if(ic==='queue'){for(let j=0;j<4;j++)walker(-60+j*40,55,.9,QCOL[j],t,j);}if(ic==='tram'){walker(0,60,1,INK,t);coin(40,-20,18,t*6);}g.restore();
    T('SIN '+s,360,y+6,76,'Anton',INK,'left');g.restore();cross(220,y,140,k(t,at,.35));});
}
function sc6(t){
  label('COMO CON EL SAR',W/2,450,k(t,EV.sar,.35),INK,YEL,60,-.03);
  const p=k(t,EV.contrato-.3,.5);if(p>0){const y=lerp(-400,820,back(p));g.save();g.translate(W/2-170,y);g.rotate(-.05);shadowed(()=>{g.fillStyle=PANEL;g.fillRect(-220,-270,440,540);},14,.3);
    T('CONTRATO DE',0,-210,44,'Anton',INK);T('ADHESIÓN',0,-160,56,'Anton',RED);g.fillStyle='rgba(234,244,255,.35)';for(let i=0;i<5;i++)g.fillRect(-170,-90+i*40,i==4?200:340,12);
    g.strokeStyle=INK;g.lineWidth=3;g.beginPath();g.moveTo(-150,200);g.lineTo(150,200);g.stroke();sig(-140,175,k(t,EV.contrato+.2,1),.95,BLUE);g.restore();tape(W/2-330,y-270,-.3);}
  stamp('1 SOLA VEZ',W/2-150,1180,70,-.12,t,EV.sola,RED);
  arrow(W/2+80,820,W/2+230,820,k(t,EV.todo-.4,.4),INK,8);
  const q=back(k(t,EV.todo-.2,.4));if(q>0){g.save();g.translate(W/2+330,860);g.scale(q,q);phone(0,0,.5,()=>{g.fillStyle=GREEN;g.fillRect(-150,-300,300,600);check(0,-20,160,k(t,EV.todo,.5),'#fff');});g.restore();
    T('TODO EN LÍNEA',W/2+330,1110,40,'Anton',GREEN);}
}
function channel(x,y,ic,s,t){g.save();g.translate(x,y);g.scale(s,s);shadowed(()=>{g.fillStyle=CREAM;g.fillRect(-140,-140,280,280);},10,.3);g.strokeStyle=INK;g.lineWidth=5;g.fillStyle=INK;
  if(ic==0){g.strokeRect(-80,-50,160,110);g.fillStyle=RED;g.fillRect(-80,-80,160,30);g.fillStyle=INK;g.fillRect(-30,10,60,50);g.beginPath();g.moveTo(-20,-90);g.quadraticCurveTo(0,-120,20,-90);g.stroke();}
  if(ic==1){g.strokeRect(-90,-60,180,120);g.fillStyle=BLUE;g.fillRect(-80,-50,160,100);g.fillStyle=INK;g.fillRect(-40,60,80,14);g.beginPath();g.moveTo(-30,-60);g.lineTo(-60,-100);g.moveTo(30,-60);g.lineTo(60,-100);g.stroke();}
  if(ic==2){const hb=1+Math.sin(t*8)*.1;g.save();g.scale(hb,hb);g.fillStyle=RED;g.beginPath();g.moveTo(0,50);g.bezierCurveTo(-90,-10,-55,-90,0,-45);g.bezierCurveTo(55,-90,90,-10,0,50);g.fill();g.restore();}
  T(['MALLS','MEDIOS','REDES'][ic],0,105,40,'Anton',INK);g.restore();}
function sc7(t){
  const p=k(t,EV.alc-.3,.5);if(p>0){const x=lerp(-500,W/2,back(p));g.save();g.translate(x-W/2,0);shadowed(()=>{g.fillStyle=CREAM;g.fillRect(90,400,900,220);},12,.3);
    g.save();g.translate(220,510);g.fillStyle='#c9bfa8';g.beginPath();g.arc(0,0,80,0,7);g.fill();g.save();g.beginPath();g.arc(0,0,80,0,7);g.clip();g.fillStyle=BLUE;g.beginPath();g.arc(0,-12,30,0,7);g.fill();g.beginPath();g.ellipse(0,66,55,52,0,Math.PI,0);g.fill();g.restore();g.strokeStyle=INK;g.lineWidth=6;g.beginPath();g.arc(0,0,80,0,7);g.stroke();g.restore();
    T('JUAN DIEGO ZELAYA',330,480,62,'Anton',INK,'left');T('Alcalde del Distrito Central',330,540,32,'Elite',INK,'left');g.restore();}
  stamp('EN LOS PRÓXIMOS DÍAS',W/2,720,46,-.04,t,EV.formal,RED);
  [[EV.malls,0],[EV.medios,1],[EV.redes,2]].forEach(([at,i])=>{const a=back(k(t,at-.15,.4));if(a<=0)return;channel(220+i*320,1000+Math.sin(t*3+i)*8,i,a*.95,t);});
  label('PARA ENSEÑAR CÓMO HACERLO',W/2,1290,k(t,EV.redes+.6,.35),INK,YEL,46,-.02);
}
function sc8(t){
  const p=k(t,EV.frase,.5);if(p>0){const y=lerp(-500,880,back(p));g.save();g.translate(W/2,y);g.rotate(-.025);shadowed(()=>{g.fillStyle=CREAM;g.fillRect(-460,-380,920,760);},16,.3);
    T('“',-360,-250,240,'Play',RED);
    T('NO SE TRATA DE',0,-170,84,'Anton',INK);T('DIGITALIZAR,',0,-80,100,'Anton',INK);
    T('SE TRATA DE',0,40,84,'Anton',INK);
    const mk=k(t,EV.reinv,.5);marker(-380,90,760,110,mk);marker(-300,200,600,110,k(t,EV.reinv+.3,.5));
    T('REINVENTAR',0,145,110,'Anton',RED);T('LA BUROCRACIA',0,255,100,'Anton',RED);
    T('— Juan Diego Zelaya',140,330,32,'Elite',INK);g.restore();tape(W/2-400,y-380,-.3);tape(W/2+400,y-370,.3);}

}
function sc9(t){
  headline('¿ESTA VEZ SÍ',470,120,INK,k(t,EV.S[8]+.05,.4));headline('VA A FUNCIONAR?',600,110,RED,k(t,EV.vez,.4));
  [['SÍ',GREEN,W/2-210,-.05],['NO',RED,W/2+210,.05]].forEach(([s,c,x,r],i)=>{const q=back(k(t,EV.vez+.5+i*.2,.35));if(q<=0)return;const wob=1+Math.sin(t*4+i*2)*.03;g.save();g.translate(x,880);g.rotate(r);g.scale(q*wob,q*wob);
    shadowed(()=>{g.fillStyle=CREAM;g.fillRect(-170,-120,340,240);},12,.3);g.strokeStyle=c;g.lineWidth=10;g.strokeRect(-150,-100,300,200);T(s,0,6,140,'Anton',c);g.restore();});
  const cp=k(t,EV.cta,.3);if(cp>0){const pul=1+Math.sin((t-EV.cta)*7)*.05;g.save();g.translate(W/2,1180);g.scale(back(cp)*pul,back(cp)*pul);shadowed(()=>{g.fillStyle=RED;rr(-260,-70,520,140,70);g.fill();},10,.35);T('COMENTÁ',0,4,84,'Anton','#fff');g.restore();
    const ht=(t-EV.cta)%1.2;hand(W/2+180,1240+(ht<.3?ht*60:ht<.5?18-(ht-.3)*90:0),ht>.25&&ht<.45?1:0);}
  confetti(t,EV.cta,W/2,1180,50);
}
const SC=[sc1,sc2,sc3,sc4,sc5,sc6,sc7,sc8,sc9];
function frame(t){g.setTransform(1,0,0,1,0,0);g.globalAlpha=1;g.drawImage(PAPER,0,0);
  if(!HITS.length)HITS=[EV.perdido,EV.acaba,EV.x1,EV.x2,EV.x3,EV.sola,EV.formal];
  const si=sceneAt(t);const [sx,sy]=shake(t);g.save();g.translate(sx,sy);enter(t,EV.S[si]);SC[si](t);g.restore();
  g.globalAlpha=1;chrome(t);subs(t,si);return cv.toDataURL('image/jpeg',.9);}
</script></body></html>
