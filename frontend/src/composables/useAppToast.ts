import { ElMessage } from "element-plus";

export type ToastType = "info" | "success" | "warning" | "error";

interface ToastOptions {
  message: string;
  type?: ToastType;
  duration?: number;
  showClose?: boolean;
}

export function useAppToast() {
  function show(options: ToastOptions) {
    ElMessage({
      message: options.message,
      type: options.type || "info",
      duration: options.duration ?? 2500,
      showClose: options.showClose ?? false,
      customClass: "app-toast",
    });
  }

  return {
    show,
    info: (message: string, duration?: number) => show({ message, type: "info", duration }),
    success: (message: string, duration?: number) => show({ message, type: "success", duration }),
    warning: (message: string, duration?: number) => show({ message, type: "warning", duration }),
    error: (message: string, duration?: number) => show({ message, type: "error", duration }),
  };
}
