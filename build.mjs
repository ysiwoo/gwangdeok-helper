// src/ 조각들을 이어 붙여 index.html(3D 모델)을 만듭니다.  실행: node build.mjs
// (게임 페이지 game.html은 이 폴더에서 뺐습니다. 원본은 Desktop\gwangdeok-campus 에 있습니다.)
import {readFileSync,writeFileSync} from 'node:fs';
const r=f=>readFileSync(new URL('./src/'+f,import.meta.url),'utf8');
const shared=['core.js','data.js','generator.js','textures.js','furniture.js','site.js'];
const pages={'index.html':['head-model.html','model.js']};
for(const [out,[head,main]] of Object.entries(pages)){writeFileSync(new URL('./'+out,import.meta.url),r(head)+shared.map(r).join('')+r(main));console.log('만듦:',out)}
