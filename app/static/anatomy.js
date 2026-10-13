import {fitProjection,slabOf,solidSvg,boxCorners,depthOf,translateAlong,cylinder} from './vendor/iso-kit.mjs';
export function mountAnatomy(host){
 const P=fitProjection(boxCorners({x:-65,y:-35,w:130,d:70,r:0},0,125),460,355,{pad:35});const parts=[];
 function add(id,x,y,w,d,z,h,tone='hi'){const plan={x,y,w,d,r:2};parts.push({id,z,center:[x+w/2,y+d/2,z+h/2],svg:solidSvg(slabOf(plan,z,h,P),{tone,crease:'lo'})})}
 add('housing',-40,-28,80,56,0,15,'lo');add('power',-33,-20,18,40,18,18,'mid');add('cpu',-10,-20,29,40,18,18,'hi');add('io',22,-20,12,40,18,18,'mid');
 for(let j=0;j<5;j++)add('terminals',-29+j*12,23,8,6,18,7,'hi');
 add('cover',-40,-28,80,56,42,5,'hi');add('display',-19,-12,38,24,48,3,'mid');
 for(let j=0;j<4;j++)add('buttons',-25+j*15,15,7,7,48,3,'lo');
 parts.sort((a,b)=>depthOf(a.center,P)-depthOf(b.center,P));host.innerHTML='<svg role="img" aria-label="Controlador modular desmontable construido con el kit Anatomy" viewBox="0 0 460 355">'+parts.map(p=>'<g data-part="'+p.id+'">'+p.svg+'</g>').join('')+'</svg>';
 return value=>{for(let p of parts){const dz=(p.id==='cover'||p.id==='display'||p.id==='buttons'?65:p.id==='housing'?0:25)*value;const dx=p.id==='power'?-20*value:p.id==='io'?20*value:0;host.querySelectorAll('[data-part="'+p.id+'"]').forEach(g=>g.setAttribute('transform',translateAlong(P,[dx,0,dz])))} };
}
