export type OAuthProvider = "google" | "kakao" | "naver";

export function isOAuthProvider(value: string): value is OAuthProvider {
  return value === "google" || value === "kakao" || value === "naver";
}

export type AuthUser = {
  id: string;
  email: string;
  nickname: string | null;
  role: string;
};

export type AuthSession = {
  user: AuthUser;
  accessToken: string;
  tokenType: "Bearer";
};

export type AuthErrorResponse = {
  error: {
    code: string;
    message: string;
    details: unknown;
    traceId: string;
  };
};
