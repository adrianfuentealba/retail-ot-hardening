import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
export function initScene(host,onSelect){
 const scene=new THREE.Scene();scene.background=new THREE.Color('#e8eeea');scene.fog=new THREE.Fog('#e8eeea',32,65);
 const cam=new THREE.PerspectiveCamera(36,1,.1,100);cam.position.set(17,15,20);
 const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.setClearColor('#e8eeea');host.appendChild(renderer.domElement);
 const controls=new OrbitControls(cam,renderer.domElement);controls.target.set(0,0,0);controls.enableDamping=true;controls.maxPolarAngle=Math.PI/2.15;controls.minDistance=9;controls.maxDistance=38;
 scene.add(new THREE.HemisphereLight(0xf7fff5,0x657c6b,2.6));const light=new THREE.DirectionalLight(0xfff9e2,3.4);light.position.set(10,22,8);light.castShadow=true;light.shadow.mapSize.set(2048,2048);light.shadow.camera.left=-16;light.shadow.camera.right=16;light.shadow.camera.top=16;light.shadow.camera.bottom=-16;scene.add(light);
 const ground=new THREE.Mesh(new THREE.PlaneGeometry(140,140),new THREE.MeshStandardMaterial({color:0xe8eeea,roughness:1}));ground.rotation.x=-Math.PI/2;ground.position.y=-.14;ground.receiveShadow=true;scene.add(ground);
 const grid=new THREE.GridHelper(75,75,0xd9e2da,0xe1e8e2);grid.position.y=-.13;scene.add(grid);
 const root=new THREE.Group();scene.add(root);const selectable=[];const fans=[];const fridges=[];const products=[];let process=null;let selected=null;
 const mats={floor:0xd8dfd5,wall:0xc2d0c0,steel:0x879c91,dark:0x325649,green:0x528d6d,cream:0xf1eee3,blue:0x6e9da8,yellow:0xdca766};
 function box(w,h,d,x,y,z,color,group=root){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),new THREE.MeshStandardMaterial({color,roughness:.7}));m.position.set(x,y,z);m.castShadow=true;m.receiveShadow=true;group.add(m);return m}
 function cyl(r,h,x,y,z,col,group=root){const m=new THREE.Mesh(new THREE.CylinderGeometry(r,r,h,20),new THREE.MeshStandardMaterial({color:col,metalness:.25,roughness:.5}));m.position.set(x,y,z);m.castShadow=true;group.add(m);return m}
 function label(text,x,y,z,color='#244a38',scale=1.0){const c=document.createElement('canvas');c.width=512;c.height=128;const ctx=c.getContext('2d');ctx.fillStyle='#f7f9f3';ctx.fillRect(0,0,512,128);ctx.font='600 36px sans-serif';ctx.fillStyle=color;ctx.textAlign='center';ctx.fillText(text,256,77);const s=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c)}));s.position.set(x,y,z);s.scale.set(3.3*scale,.83*scale,1);root.add(s);return s}
 function tag(group,id){group.traverse(o=>{if(o.isMesh){o.userData.asset=id;selectable.push(o)}})}
 function tube(points,r,col){const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));const m=new THREE.Mesh(new THREE.TubeGeometry(curve,30,r,8,false),new THREE.MeshStandardMaterial({color:col,roughness:.5,metalness:.2}));m.castShadow=true;root.add(m);return m}
 box(17,.25,13,0,0,0,mats.floor);box(17,1.4,.15,0,.8,-6.5,mats.wall);box(.15,1.4,13,-8.5,.8,0,mats.wall);box(.2,.06,12.8,-1,.15,0,0xf1f2e8);
 // Shelves, individual products and checkout create a readable cutaway supermarket.
 for(let row=0;row<3;row++){
  const x=-5.5+row*3;const g=new THREE.Group();root.add(g);box(2,.2,4.1,x,.3,.6,mats.dark,g);
  for(let k=0;k<3;k++){box(2,.1,4.1,x,.7+k*.5,.6,mats.cream,g);for(let j=0;j<9;j++)for(let side of [-.58,.58])box(.36,.34,.23,x+side,.93+k*.5,-1.18+j*.43,[0xb7bf74,0xc88d62,0x8cac92][k],g)}tag(g,'shelf')
 }
 const cold=new THREE.Group();root.add(cold);
 for(let j=0;j<3;j++){
  const x=-5.7+j*4.3;box(3.8,.25,1.45,x,.38,-4.7,mats.dark,cold);const body=box(3.8,1.3,1.4,x,1.12,-4.7,mats.blue,cold);fridges.push(body);box(3.9,.13,1.55,x,1.82,-4.7,mats.cream,cold);
  for(let k=0;k<3;k++){box(3.4,.06,.75,x,.67+k*.38,-4.48,mats.cream,cold);for(let p=0;p<8;p++){const m=box(.24,.21,.27,x-1.4+p*.4,.81+k*.38,-4.36,k===1?0xebcc93:0xadc584,cold);products.push(m)}}
  for(let k=0;k<4;k++)box(.045,1.23,.06,x-1.8+k*1.2,1.14,-3.98,mats.steel,cold);
 }tag(cold,'cold');label('CADENA DE FRÍO',-1.2,2.9,-4.8);
 const machine=new THREE.Group();root.add(machine);box(3.5,.28,2.5,5.9,.3,.6,mats.dark,machine);
 for(let j=0;j<3;j++){cyl(.38,.72,5.0+j*.85,.83,.2,mats.steel,machine);box(.58,.43,.9,5.0+j*.85,.64,1.05,mats.dark,machine)}
 box(3.2,1.6,.22,5.9,1.3,1.8,mats.cream,machine);
 for(let j=0;j<3;j++){let f=new THREE.Group();f.position.set(5.05+j*.86,1.35,1.94);machine.add(f);for(let k=0;k<4;k++){let b=box(.51,.11,.035,0,0,0,mats.steel,f);b.rotation.z=k*Math.PI/2;b.position.set(Math.cos(k*Math.PI/2)*.16,Math.sin(k*Math.PI/2)*.16,0)}fans.push(f)}
 tube([[5.2,1.5,-.1],[5.2,2.3,-.1],[5.2,2.3,-5.5],[-5.8,2.3,-5.5]],.07,0xa9b9b2);tube([[6.1,.7,0],[6.1,.7,-5.7],[-5.8,.7,-5.7]],.06,0xc4a66e);tag(machine,'compressor');label('RACK COMPRESORES',5.8,3.1,.7,'#244a38',.8);
 const cabinet=new THREE.Group();root.add(cabinet);box(1.4,2.4,.8,7,1.45,-3.7,mats.dark,cabinet);box(1.12,2.05,.13,7,1.4,-3.2,mats.cream,cabinet);
 for(let j=0;j<3;j++)box(.83,.23,.13,7,.9+j*.36,-3.07,j===1?0x56876f:0x8ba393,cabinet);box(.46,.37,.06,7,2.06,-3.01,0xabc48b,cabinet);for(let j=0;j<4;j++)cyl(.025,.08,6.64+j*.22,.66,-2.99,0xd1b871,cabinet);tag(cabinet,'plc');label('PLC-R01',7,3.4,-3.7,'#244a38',.65);
 const hmi=new THREE.Group();root.add(hmi);box(2,.15,1.2,3.0,1.05,4.6,mats.cream,hmi);for(let x of [2.25,3.75])for(let z of [4.2,5.0])box(.09,1,.09,x,.55,z,mats.dark,hmi);box(1.25,.78,.13,3,1.7,4.75,mats.dark,hmi);box(1.09,.59,.02,3,1.7,4.66,0x8ab8a0,hmi);box(.13,.28,.13,3,1.24,4.7,mats.steel,hmi);box(.82,.05,.3,3,1.18,4.2,mats.dark,hmi);tag(hmi,'hmi');label('HMI · L2',3,2.9,4.7,'#244a38',.7);
 for(let j=0;j<2;j++){box(2,.8,.9,-5+j*3,.66,4.85,mats.green);box(2.1,.12,1,-5+j*3,1.13,4.85,mats.cream);box(.38,.42,.14,-5+j*3,1.4,5.0,mats.dark)}
 // Electrical cabinet and independent schematic safety sensor.
 const electric=new THREE.Group();root.add(electric);box(1.25,2.1,.75,7,1.2,4.55,mats.steel,electric);box(1.03,1.89,.1,7,1.2,4.12,mats.cream,electric);box(.29,.29,.02,7,1.9,4.05,mats.yellow,electric);tag(electric,'electrical');
 const sensor=new THREE.Group();root.add(sensor);box(.32,.25,.26,1.4,2,-4.75,mats.cream,sensor);cyl(.04,.18,1.4,2.21,-4.75,mats.steel,sensor);tag(sensor,'sensor');
 // Logistics loading strip is context, not a separately instrumented store.
 box(4.5,.12,3.3,11,.02,-1,0xc5cfc5);box(2.5,1.35,1.45,11,.79,-1,mats.cream);box(.8,1.02,1.42,12.65,.6,-1,mats.green);for(let x of [10.2,11.8,12.8])for(let z of [-1.7,-.3]){let wheel=cyl(.24,.13,x,.31,z,0x3c4a40);wheel.rotation.x=Math.PI/2}label('ABASTECIMIENTO',11,2.9,-1,'#244a38',.75);
 label('SCL-01 / RETAIL OT',-3,.7,7.2,'#244a38',1.0);
 const warning=new THREE.Group();warning.position.set(0,3.1,-4.7);root.add(warning);const halo=cyl(.34,.08,0,0,0,0xd78642,warning);warning.visible=false;
 const ray=new THREE.Raycaster();const pointer=new THREE.Vector2();let down;
 renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;let rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(pointer,cam);let hit=ray.intersectObjects(selectable,false)[0];if(hit){selected=hit.object.userData.asset;onSelect(selected)}});
 const observer=new ResizeObserver(()=>{let w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;renderer.setSize(w,h,false);cam.aspect=w/h;cam.updateProjectionMatrix()});observer.observe(host);
 const clock=new THREE.Clock();let frame=0;const reduced=matchMedia('(prefers-reduced-motion: reduce)');function loop(){requestAnimationFrame(loop);const dt=Math.min(clock.getDelta(),.1);if(document.hidden)return;frame+=dt;if(process&&!reduced.matches){for(let f of fans)f.rotation.z+=dt*(process.compressor?3:.1);warning.rotation.y+=dt*.5}controls.update();renderer.render(scene,cam)}loop();
 return {update(p){process=p;if(!p)return;const danger=p.temperature>8;const signalFault=!p.sensor_connected||Math.abs((p.measured_temperature??p.temperature)-p.temperature)>3;sensor.traverse(o=>{if(o.isMesh)o.material.color.set(signalFault?0xda8c4b:0xadc48f)});cabinet.traverse(o=>{if(o.isMesh&&o.geometry.type==='BoxGeometry')o.material.emissive.set(p.fallback_active?0x241200:0x000000)});fridges.forEach(m=>m.material.color.set(danger?0xd39569:0x6e9da8));products.forEach(m=>m.material.color.set(p.spoiled?0x967354:0xb2c58f));warning.visible=p.thermal_risk||p.fallback_active;},overview(){cam.position.set(17,15,20);controls.target.set(0,0,0)},focus(id){const loc={plc:[7,1.4,-3.7],hmi:[3,1.4,4.6],compressor:[5.9,1,.6],cold:[-1.3,1,-4.7],sensor:[1.4,2,-4.75],electrical:[7,1.2,4.5]}[id];if(loc){controls.target.set(...loc);cam.position.set(loc[0]+6,loc[1]+5,loc[2]+7)}}};
}
