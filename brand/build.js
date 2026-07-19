const sharp = require('sharp');
const fs = require('fs');

const ROSE_HI='#F5386A', ROSE='#E11D48', STONE900='#1c1917', STONE950='#0c0a09';
const CREAM='#faf7f5', STONE800='#292524', STONE500='#78716c', STONE400='#a8a29e';

const zDefs = `
  <linearGradient id="zg" x1="0" y1="0" x2="0.4" y2="1">
    <stop offset="0" stop-color="${ROSE_HI}"/><stop offset="1" stop-color="${ROSE}"/>
  </linearGradient>`;

// z mark centered in a 400-box; scale s and translate (tx,ty) to place it
function zPath(stroke, sw=44){
  return `<path d="M120 150 H280 L120 250 H280" fill="none" stroke="${stroke}"
     stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round"/>`;
}

function icon({bg1,bg2,mark}){
  return `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
   <defs>
     <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${bg1}"/><stop offset="1" stop-color="${bg2}"/></linearGradient>
     ${zDefs}
   </defs>
   <rect width="400" height="400" rx="92" fill="url(#bg)"/>${mark}</svg>`;
}

const icons = {
  'zabt-icon-dark':  icon({bg1:STONE900,bg2:STONE950,mark:zPath('url(#zg)')}),
  'zabt-icon-rose':  icon({bg1:ROSE_HI,bg2:ROSE,mark:zPath(CREAM)}),
  'zabt-icon-light': icon({bg1:'#ffffff',bg2:'#f5f5f4',mark:zPath('url(#zg)')}),
};

// mini z-squircle for lockups (draw inline, no external ref)
function miniIcon(x,y,size,{bg1,bg2,stroke}){
  const s=size/400; const gid='mz'+x;
  const strokeVal = stroke==='grad' ? `url(#${gid})` : stroke;
  return `<g transform="translate(${x},${y}) scale(${s})">
    <defs>
      <linearGradient id="mbg${x}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${bg1}"/><stop offset="1" stop-color="${bg2}"/></linearGradient>
      <linearGradient id="${gid}" x1="0" y1="0" x2="0.4" y2="1"><stop offset="0" stop-color="${ROSE_HI}"/><stop offset="1" stop-color="${ROSE}"/></linearGradient>
    </defs>
    <rect width="400" height="400" rx="92" fill="url(#mbg${x})"/>
    <path d="M120 150 H280 L120 250 H280" fill="none" stroke="${strokeVal}" stroke-width="44" stroke-linecap="round" stroke-linejoin="round"/>
  </g>`;
}

function wordmark({w,h,bg,icoBg1,icoBg2,icoStroke,zabtColor,aiColor,tagColor,tagline}){
  const icoSize=Math.round(h*0.62), icoY=Math.round((h-icoSize)/2), icoX=Math.round(h*0.28);
  const textX=icoX+icoSize+Math.round(h*0.24);
  const fs=Math.round(h*0.34);
  const tag = tagline ? `<text x="${textX+3}" y="${h*0.5+fs*0.62+fs*0.42}" font-family="Inter, Helvetica, Arial, sans-serif" font-size="${Math.round(fs*0.34)}" font-weight="500" letter-spacing="0.5" fill="${tagColor}">${tagline}</text>` : '';
  const baseY = tagline ? h*0.5+fs*0.18 : h*0.5+fs*0.36;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
   ${bg?`<rect width="${w}" height="${h}" fill="${bg}"/>`:''}
   ${miniIcon(icoX,icoY,icoSize,{bg1:icoBg1,bg2:icoBg2,stroke:icoStroke})}
   <text x="${textX}" y="${baseY}" font-family="Inter, Helvetica, Arial, sans-serif" font-size="${fs}" font-weight="700" letter-spacing="-1">
     <tspan fill="${zabtColor}">zabt</tspan><tspan fill="${aiColor}">.ai</tspan></text>
   ${tag}</svg>`;
}

(async()=>{
  // Icons at multiple sizes
  for (const [n,svg] of Object.entries(icons)){
    fs.writeFileSync(`brand/${n}.svg`, svg);
    for (const sz of [400,800,1024]){
      await sharp(Buffer.from(svg)).resize(sz,sz).png().toFile(`brand/${n}-${sz}.png`);
    }
  }
  // Wordmark lockups (transparent-ish; provide dark + light)
  const wmDark = wordmark({w:1000,h:280,bg:null,icoBg1:STONE900,icoBg2:STONE950,icoStroke:'grad',zabtColor:CREAM,aiColor:ROSE,tagColor:STONE400});
  const wmLight= wordmark({w:1000,h:280,bg:null,icoBg1:STONE900,icoBg2:STONE950,icoStroke:'grad',zabtColor:STONE900,aiColor:ROSE,tagColor:STONE500});
  fs.writeFileSync('brand/zabt-wordmark-dark.svg', wmDark);
  fs.writeFileSync('brand/zabt-wordmark-light.svg', wmLight);
  await sharp(Buffer.from(wmDark)).png().toFile('brand/zabt-wordmark-dark.png');
  await sharp(Buffer.from(wmLight)).png().toFile('brand/zabt-wordmark-light.png');

  // LinkedIn personal banner 1584x396
  const banner = wordmark({w:1584,h:396,bg:STONE950,icoBg1:STONE800,icoBg2:STONE950,icoStroke:'grad',zabtColor:CREAM,aiColor:ROSE,tagColor:STONE400,tagline:'Self-hosted AI meeting intelligence'});
  fs.writeFileSync('brand/zabt-linkedin-banner.svg', banner);
  await sharp(Buffer.from(banner)).png().toFile('brand/zabt-linkedin-banner.png');

  console.log('built', fs.readdirSync('brand').filter(f=>f.endsWith('.png')).length, 'PNGs');
})().catch(e=>console.log('ERR',e.message));
