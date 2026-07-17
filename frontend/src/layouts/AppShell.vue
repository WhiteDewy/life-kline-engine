<template>
  <div class="shell">
    <SiteHeader
      :logged-in="loggedIn"
      :user-phone="userPhone"
      @login="$emit('login')"
      @history="$emit('history')"
    />
    <main class="content">
      <slot />
    </main>
    <SiteFooter @help="$emit('help')" @history="$emit('history')" />
  </div>
</template>

<script setup lang="ts">
import SiteHeader from "@/components/SiteHeader.vue";
import SiteFooter from "@/components/SiteFooter.vue";

defineProps<{
  loggedIn?: boolean;
  userPhone?: string;
}>();

defineEmits<{
  login: [];
  history: [];
}>();
</script>

<style scoped>
.shell {
  min-height: 100vh;
  background: var(--bg);
}
.content {
  width: 100%;
  max-width: var(--page-shell-max);
  margin: 0 auto;
  padding: calc(var(--h-header)) 0 0;
}
</style>
