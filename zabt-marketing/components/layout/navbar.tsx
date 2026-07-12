"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { navLinks, ctaLinks } from "@/content/navigation";

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 backdrop-blur-lg bg-white/80 border-b border-border/50">
      <nav className="max-w-6xl mx-auto flex items-center justify-between h-16 px-6">
        {/* Logo */}
        <Link href="/" className="text-xl font-bold text-stone-900 tracking-tight">
          Zabt
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-stone-600 hover:text-stone-900 transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Desktop CTAs */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href={ctaLinks.signIn.href}
            className="text-sm font-medium text-stone-600 hover:text-stone-900 transition-colors px-3 py-2"
          >
            {ctaLinks.signIn.label}
          </Link>
          <Link
            href={ctaLinks.getStarted.href}
            className="bg-primary text-white text-sm font-medium rounded-lg px-4 py-2 hover:opacity-90 transition-opacity"
          >
            {ctaLinks.getStarted.label}
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2 text-stone-600"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle navigation"
        >
          {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
        </button>
      </nav>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="md:hidden border-t border-border/50 bg-white px-6 py-4 space-y-3">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="block text-sm font-medium text-stone-600 py-2"
              onClick={() => setMobileOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <div className="flex flex-col gap-2 pt-3 border-t border-border/50">
            <Link
              href={ctaLinks.signIn.href}
              className="text-sm font-medium text-stone-600 py-2"
            >
              {ctaLinks.signIn.label}
            </Link>
            <Link
              href={ctaLinks.getStarted.href}
              className="bg-primary text-white text-sm font-medium rounded-lg px-4 py-2.5 text-center"
            >
              {ctaLinks.getStarted.label}
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
