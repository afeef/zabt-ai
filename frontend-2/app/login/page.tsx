// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import {
  socialLogin,
  ssoLookup,
  loginWithRememberMe,
  type OAuthProvider,
} from "@/app/lib/api";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { SocialButton } from "@/app/components/ui/social-button";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSocialLogin = async (provider: OAuthProvider) => {
    await socialLogin(provider);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const ssoResult = await ssoLookup(email);
      if (ssoResult.sso_enabled && ssoResult.redirect_url) {
        window.location.href = ssoResult.redirect_url;
        return;
      }
      await loginWithRememberMe(email, password, rememberMe);
      router.push("/");
    } catch {
      setError("Incorrect email or password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-stone-50 px-4">
      <div className="w-full max-w-md bg-white rounded-lg border border-stone-200 p-8">
        {/* Logo + heading */}
        <div className="mb-6">
          <p className="text-xl font-bold text-stone-900 mb-4">Zabt</p>
          <h1 className="text-2xl font-bold text-stone-900 mb-1">
            Welcome back
          </h1>
          <p className="text-sm text-stone-500">
            Please enter your details to sign in.
          </p>
        </div>

        {/* Social login buttons */}
        <div className="space-y-3 mb-6">
          <SocialButton
            provider="google"
            label="Sign in with Google"
            onClick={() => handleSocialLogin("google")}
          />
          <SocialButton
            provider="microsoft"
            label="Sign in with Microsoft"
            onClick={() => handleSocialLogin("microsoft")}
          />
        </div>

        {/* Separator */}
        <div className="flex items-center gap-3 mb-6">
          <hr className="flex-1 border-stone-200" />
          <span className="text-xs text-stone-400">or sign in with email</span>
          <hr className="flex-1 border-stone-200" />
        </div>

        {/* Email / password form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">
              Email address
            </label>
            <Input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">
              Password
            </label>
            <div className="relative">
              <Input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pr-10"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-stone-400 hover:text-stone-600"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <EyeOff size={16} />
                ) : (
                  <Eye size={16} />
                )}
              </button>
            </div>
          </div>

          {/* Remember me + Forgot password */}
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm text-stone-700 cursor-pointer">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="rounded border-stone-300 text-primary focus:ring-primary"
              />
              Remember me
            </label>
            <Link
              href="/forgot-password"
              className="text-sm text-primary hover:underline"
            >
              Forgot password?
            </Link>
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <Button type="submit" loading={loading} className="w-full">
            Sign in
          </Button>
        </form>

        <p className="mt-6 text-sm text-stone-500 text-center">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-primary hover:underline">
            Register
          </Link>
        </p>
      </div>
    </main>
  );
}
