export const config = {
  api: {
    userServiceUrl:
      import.meta.env.VITE_USER_SERVICE_URL || "http://localhost:8001",
    subscriptionServiceUrl:
      import.meta.env.VITE_SUBSCRIPTION_SERVICE_URL || "http://localhost:8011",
    paymentServiceUrl:
      import.meta.env.VITE_PAYMENT_SERVICE_URL || "http://localhost:8013",
    schedulerServiceUrl:
      import.meta.env.VITE_SCHEDULER_SERVICE_URL || "http://localhost:8014",
  },
  app: {
    name: "Admin Panel",
  },
} as const;
