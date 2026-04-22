"use client";

import { useRef, useState, useEffect, KeyboardEvent, ClipboardEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { LayoutDashboard, Mail } from "lucide-react";
import { useVerifyEmail, useResendVerification } from "@/queries/auth";
import { getApiError } from "@/lib/apiError";

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") ?? "";

  const [digits, setDigits] = useState<string[]>(["", "", "", "", "", ""]);
  const [error, setError] = useState("");
  const [resendCooldown, setResendCooldown] = useState(60);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const verify = useVerifyEmail();
  const resend = useResendVerification();

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = setTimeout(() => setResendCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [resendCooldown]);

  const otp = digits.join("");

  function handleDigitChange(index: number, value: string) {
    if (!/^\d?$/.test(value)) return;
    const next = [...digits];
    next[index] = value;
    setDigits(next);
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  }

  function handleKeyDown(index: number, e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  }

  function handlePaste(e: ClipboardEvent<HTMLInputElement>) {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    const next = [...digits];
    for (let i = 0; i < pasted.length; i++) next[i] = pasted[i];
    setDigits(next);
    const focusIndex = Math.min(pasted.length, 5);
    inputRefs.current[focusIndex]?.focus();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (otp.length < 6) return;
    setError("");
    try {
      await verify.mutateAsync({ email, otp });
      router.push("/dashboard");
    } catch (err) {
      setError(getApiError(err, "Invalid or expired code. Please try again."));
      setDigits(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    }
  }

  async function handleResend() {
    if (resendCooldown > 0 || !email) return;
    try {
      await resend.mutateAsync(email);
      setResendCooldown(60);
      setError("");
    } catch (err) {
      setError(getApiError(err, "Failed to resend code. Please try again."));
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="mb-8 flex items-center justify-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary">
            <LayoutDashboard className="h-5 w-5 text-primary-foreground" />
          </div>
        </div>

        {/* Icon + heading */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
            <Mail className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-2xl font-bold">Check your email</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            We sent a 6-digit code to{" "}
            <span className="font-medium text-foreground">{email || "your email"}</span>
          </p>
        </div>

        {error && (
          <div className="mb-5 rounded-lg border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 6-digit input */}
          <div className="flex justify-center gap-3">
            {digits.map((digit, i) => (
              <input
                key={i}
                ref={(el) => { inputRefs.current[i] = el; }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleDigitChange(i, e.target.value)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                onPaste={handlePaste}
                className="h-14 w-12 rounded-xl border border-input bg-background text-center text-xl font-semibold focus:border-primary focus:outline-none focus:ring-2 focus:ring-ring"
              />
            ))}
          </div>

          <button
            type="submit"
            disabled={otp.length < 6 || verify.isPending}
            className="flex h-10 w-full items-center justify-center rounded-lg bg-primary text-sm font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {verify.isPending ? "Verifying…" : "Verify email"}
          </button>
        </form>

        {/* Resend */}
        <p className="mt-6 text-center text-sm text-muted-foreground">
          Didn&apos;t receive a code?{" "}
          {resendCooldown > 0 ? (
            <span className="text-muted-foreground">
              Resend in {resendCooldown}s
            </span>
          ) : (
            <button
              onClick={handleResend}
              disabled={resend.isPending}
              className="font-medium text-primary hover:underline disabled:opacity-50"
            >
              {resend.isPending ? "Sending…" : "Resend code"}
            </button>
          )}
        </p>

        <p className="mt-3 text-center text-sm text-muted-foreground">
          <Link href="/auth/login" className="font-medium text-primary hover:underline">
            Back to sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
