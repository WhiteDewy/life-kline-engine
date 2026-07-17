<template>
  <AppShell
    :logged-in="isLoggedIn"
    :user-phone="user?.phone"
    @login="showLogin = true"
    @history="goHistory"
  >
    <router-view />
  </AppShell>

  <LoginModal
    :visible="showLogin"
    @close="showLogin = false"
    @logged-in="onLoggedIn"
  />
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import AppShell from "@/layouts/AppShell.vue";
import LoginModal from "@/components/LoginModal.vue";
import { useAuth } from "@/utils/auth";

const router = useRouter();
const { user, isLoggedIn, loadMe } = useAuth();
const showLogin = ref(false);

onMounted(() => loadMe());

function onLoggedIn() {
  showLogin.value = false;
}

function goHistory() {
  router.push({ name: "history" });
}
</script>
