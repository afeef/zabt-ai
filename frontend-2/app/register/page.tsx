"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { register, socialLogin, type OAuthProvider } from "@/app/lib/api";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { SocialButton } from "@/app/components/ui/social-button";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSocialSignUp = async (provider: OAuthProvider) => {
    await socialLogin(provider);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(email, password, fullName);
      router.push("/");
    } catch (err: unknown) {
      const status =
        err &&
          typeof err === "object" &&
          "response" in err &&
          err.response &&
          typeof err.response === "object" &&
          "status" in err.response
          ? (err.response as { status: number }).status
          : null;
      if (status === 400) {
        setError("This email is already registered. Try signing in instead.");
      } else {
        setError("Registration is temporarily unavailable. Please try again.");
      }
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
            Create your account
          </h1>
          <p className="text-sm text-stone-500">
            Please enter your details to sign in.
          </p>
        </div>

        {/* Social sign-up buttons */}
        <div className="space-y-3 mb-6">
          <SocialButton
            provider="google"
            label="Sign up with Google"
            onClick={() => handleSocialSignUp("google")}
          />
          <SocialButton
            provider="microsoft"
            label="Sign up with Microsoft"
            onClick={() => handleSocialSignUp("microsoft")}
          />
        </div>

        {/* Separator */}
        <div className="flex items-center gap-3 mb-6">
          <hr className="flex-1 border-stone-200" />
          <span className="text-xs text-stone-400">or sign up with email</span>
          <hr className="flex-1 border-stone-200" />
        </div>

        {/* Registration form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">
              Full name
            </label>
            <Input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="John Doe"
            />
          </div>

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
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pr-10"
                placeholder="At least 8 characters"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-stone-400 hover:text-stone-600"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <Button type="submit" loading={loading} className="w-full">
            Sign up
          </Button>
        </form>

        <p className="mt-6 text-sm text-stone-500 text-center">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
