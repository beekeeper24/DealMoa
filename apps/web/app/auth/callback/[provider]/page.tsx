import { notFound } from "next/navigation";

import { AuthCallbackPage } from "@/auth/AuthCallbackPage";
import { isOAuthProvider } from "@/auth/types";

type AuthCallbackRouteProps = {
  params: Promise<{
    provider: string;
  }>;
};

export default async function AuthCallbackRoute({ params }: AuthCallbackRouteProps) {
  const { provider } = await params;
  if (!isOAuthProvider(provider)) {
    notFound();
  }
  return <AuthCallbackPage provider={provider} />;
}
