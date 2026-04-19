"use client";

import Link from "next/link";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Moon, Sun } from "lucide-react";
import { ROUTES } from "@/constants/routes";

export function Navbar() {
  const { resolvedTheme, setTheme } = useTheme();

  return (
    <nav className="border-b bg-background px-4 py-3">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <Link href={ROUTES.dashboard} className="text-lg font-semibold">
          Boilerplate
        </Link>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
            aria-label="Toggle theme"
          >
            <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>
        </div>
      </div>
    </nav>
  );
}
