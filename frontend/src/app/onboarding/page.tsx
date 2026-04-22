"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { Rocket, Building2, User } from "lucide-react";
import { toast } from "sonner";

import { authService } from "@/services/auth";
import { useMe } from "@/queries/auth";
import { useInvitations } from "@/queries/invitations";
import { InvitationCard } from "@/components/shared/InvitationCard";

export default function OnboardingPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: me, isLoading: userLoading } = useMe();
  const { data: invitations, isLoading: invLoading } = useInvitations();

  const [step, setStep] = useState(1);
  const [fullName, setFullName] = useState("");
  const [orgName, setOrgName] = useState("");
  const [isFinalizing, setIsFinalizing] = useState(false);

  useEffect(() => {
    if (me?.full_name && !fullName) {
      setFullName(me.full_name);
    }
  }, [me, fullName]);

  if (userLoading || invLoading) return null;

  if (me?.onboarding_completed_at) {
    router.push("/dashboard");
    return null;
  }

  const hasInvitations = invitations && invitations.length > 0;

  async function handleComplete(finalOrgName?: string) {
    if (!fullName) {
      toast.error("Please enter your name");
      return;
    }

    setIsFinalizing(true);
    try {
      await authService.completeOnboarding(fullName, finalOrgName || "");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["me"] }),
        queryClient.invalidateQueries({ queryKey: ["orgs"] }),
      ]);
      toast.success("Welcome aboard!");
      router.push("/dashboard");
    } catch (err) {
      toast.error("Failed to complete onboarding");
    } finally {
      setIsFinalizing(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-border bg-card p-8 shadow-xl">
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-lg">
            <Rocket className="h-6 w-6 text-primary-foreground" />
          </div>
          <h1 className="mt-6 text-2xl font-bold tracking-tight">Let&apos;s get started</h1>
          <p className="mt-2 text-sm text-muted-foreground">Setup your workspace in just a few steps.</p>
        </div>

        {/* Progress dots */}
        <div className="flex justify-center gap-2">
          <div className={`h-1.5 w-8 rounded-full transition-colors ${step === 1 ? "bg-primary" : "bg-muted"}`} />
          {hasInvitations && <div className={`h-1.5 w-8 rounded-full transition-colors ${step === 2 ? "bg-primary" : "bg-muted"}`} />}
          <div className={`h-1.5 w-8 rounded-full transition-colors ${step === 3 || (!hasInvitations && step === 2) ? "bg-primary" : "bg-muted"}`} />
        </div>

        <div className="mt-8 space-y-6">
          {step === 1 && (
            <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <User className="h-4 w-4" /> Your Full Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jane Doe"
                  className="flex h-11 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
              </div>
              <button
                onClick={() => fullName && setStep(hasInvitations ? 2 : 3)}
                disabled={!fullName}
                className="flex h-11 w-full items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-all hover:opacity-90 disabled:opacity-50"
              >
                Continue
              </button>
            </div>
          )}

          {step === 2 && hasInvitations && (
            <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="text-center space-y-1">
                <h3 className="font-semibold">Pending Invitations</h3>
                <p className="text-xs text-muted-foreground">You were invited to these organizations</p>
              </div>
              
              <div className="space-y-4 max-h-[300px] overflow-y-auto px-1 py-1">
                {invitations.map((inv) => (
                  <InvitationCard 
                    key={inv.id} 
                    invitation={inv} 
                    onSuccess={() => handleComplete()}
                  />
                ))}
              </div>

              <div className="flex flex-col gap-3 pt-2">
                <button
                  onClick={() => setStep(3)}
                  className="text-xs font-medium text-muted-foreground hover:text-foreground underline text-center"
                >
                  None of these? Create a new organization
                </button>
                <button
                  onClick={() => setStep(1)}
                  className="flex h-11 w-full items-center justify-center rounded-lg border border-input bg-background px-4 py-2 text-sm font-semibold transition-colors hover:bg-muted"
                >
                  Back
                </button>
              </div>
            </div>
          )}

          {(step === 3 || (step === 2 && !hasInvitations)) && (
            <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Building2 className="h-4 w-4" /> Company or Organization Name
                </label>
                <input
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder="Acme Corp"
                  className="flex h-11 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setStep(hasInvitations ? 2 : 1)}
                  className="flex h-11 flex-1 items-center justify-center rounded-lg border border-input bg-background px-4 py-2 text-sm font-semibold transition-colors hover:bg-muted"
                >
                  Back
                </button>
                <button
                  onClick={() => handleComplete(orgName)}
                  disabled={!orgName || isFinalizing}
                  className="flex h-11 flex-[2] items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-all hover:opacity-90 disabled:opacity-50"
                >
                  {isFinalizing ? "Finalizing…" : "Finish Setup"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
