<template>
  <transition name="gloss-fade">
    <div class="gloss-overlay" v-if="visible" @click.self="$emit('close')">
      <div class="gloss-panel">
        <div class="gloss-head">
          <h3>📖 星灵小词典</h3>
          <button class="gloss-close" @click="$emit('close')">✕</button>
        </div>
        <p class="gloss-sub">占星术语，用最简单的话说给你听</p>
        <div class="gloss-list">
          <div v-for="item in glossary" :key="item.term" class="gloss-item">
            <span class="gloss-term">{{ item.term }}</span>
            <span class="gloss-def">{{ item.def }}</span>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
defineProps<{ visible: boolean }>();
defineEmits<{ close: [] }>();

const glossary = [
  { term: "庙旺", def: "行星在自己最舒服的星座里——像回到家一样自在，能量发挥得最好。" },
  { term: "失势", def: "行星在自己最不舒服的星座之一——像穿了不合脚的鞋，但还是能走路。" },
  { term: "落陷", def: "行星最难的落点——像逆风骑车上坡。不是做不到，是更费力。这个位置往往是你成长最多的地方。" },
  { term: "命主星", def: "你出生时上升星座的守护星。它是你这辈子的'主线任务'——你性格的核心、人生的方向盘。" },
  { term: "飞星", def: "一个宫的守护星飞去了另一个宫——像把A房间的钥匙放在了B房间，两个宫的故事就连在了一起。" },
  { term: "法达", def: "一种时间分割法。把你的生命分成不同的'章节'，每个章节由一颗行星掌管——像一本书按行星分章。" },
  { term: "接纳", def: "行星A落在行星B守护的星座里，B愿意'收留'A——像一位前辈在暗中帮你。" },
  { term: "互溶", def: "两颗行星互相落在对方守护的星座里——互相收留，像一个牢固的契约。这是星盘里最强的连接之一。" },
  { term: "宫位", def: "星盘的12个区域。每个区域管你人生的一个领域——1宫是你自己，2宫是钱财，7宫是伴侣，10宫是事业...依此类推。" },
  { term: "角宫/续宫/果宫", def: "角宫(1/4/7/10)力量最强，像房子的承重墙。续宫(2/5/8/11)次之，果宫(3/6/9/12)最弱——但不代表不重要，只是能量的'密度'不同。" },
  { term: "相位", def: "两颗行星之间的角度关系。合相(0°)是并肩走，三分(120°)是顺路，四分(90°)是吵架，对分(180°)是面对面——每种关系都是一种对话。" },
  { term: "发光体", def: "太阳和月亮的合称。太阳是你的核心意志，月亮是你的情绪本能——它们是你星盘里最亮的两盏灯。" },
  { term: "上升星座", def: "你出生时东方地平线上的星座。它不是你的'面具'——是你和世界打交道的第一反应方式，也是别人对你的第一印象。" },
  { term: "古占/现占", def: "古典占星看客观事件('这件事难不难')，现代占星看心理体验('你在这件事里感受到什么')。两者不矛盾——一个看结构，一个看温度。" },
];
</script>

<style scoped>
.gloss-overlay {
  position: fixed; inset: 0; z-index: 500;
  display: flex; align-items: center; justify-content: center; padding: 20px;
  background: rgba(0,0,0,0.3); backdrop-filter: blur(6px);
}
.gloss-panel {
  width: 100%; max-width: 420px; max-height: 80vh; overflow-y: auto;
  padding: 24px 22px; border-radius: 24px;
  background: rgba(255,255,255,0.96); box-shadow: 0 16px 48px rgba(0,0,0,0.12);
}
.gloss-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.gloss-head h3 { margin: 0; font-size: 18px; color: #4a3728; }
.gloss-close {
  width: 30px; height: 30px; border-radius: 50%; border: none;
  background: rgba(0,0,0,0.04); color: #8b7355; cursor: pointer; font-size: 14px;
}
.gloss-sub { font-size: 12px; color: #a89880; margin: 0 0 16px; }
.gloss-list { display: flex; flex-direction: column; gap: 10px; }
.gloss-item {
  padding: 12px 14px; border-radius: 14px; background: rgba(0,0,0,0.02);
  border: 1px solid rgba(0,0,0,0.04);
}
.gloss-term { display: block; font-size: 14px; font-weight: 700; color: #4a3728; margin-bottom: 3px; }
.gloss-def { display: block; font-size: 13px; color: #6b5744; line-height: 1.6; }
.gloss-fade-enter-active { transition: all 0.3s ease; }
.gloss-fade-leave-active { transition: all 0.2s ease; }
.gloss-fade-enter-from { opacity: 0; }
.gloss-fade-leave-to { opacity: 0; }
</style>
