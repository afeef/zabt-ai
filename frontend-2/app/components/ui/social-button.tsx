import type { OAuthProvider } from "@/app/lib/api";
import { Button } from "@/app/components/ui/button";
import { JSX } from "react";

interface SocialButtonProps {
  provider: OAuthProvider;
  label: string;
  onClick: () => void;
}

const GoogleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
    <path
      d="M19.6 10.227c0-.709-.064-1.39-.182-2.045H10v3.868h5.382a4.6 4.6 0 0 1-1.996 3.018v2.51h3.232c1.891-1.742 2.982-4.305 2.982-7.35Z"
      fill="#4285F4"
    />
    <path
      d="M10 20c2.7 0 4.964-.895 6.618-2.423l-3.232-2.509c-.895.6-2.04.955-3.386.955-2.605 0-4.81-1.76-5.595-4.123H1.064v2.59A9.996 9.996 0 0 0 10 20Z"
      fill="#34A853"
    />
    <path
      d="M4.405 11.9A6.01 6.01 0 0 1 4.09 10c0-.663.114-1.308.314-1.9V5.51H1.063A9.996 9.996 0 0 0 0 10c0 1.614.386 3.14 1.064 4.49L4.405 11.9Z"
      fill="#FBBC05"
    />
    <path
      d="M10 3.977c1.468 0 2.786.505 3.822 1.496l2.868-2.868C14.959.992 12.695 0 10 0A9.996 9.996 0 0 0 1.064 5.51L4.405 8.1C5.19 5.736 7.395 3.977 10 3.977Z"
      fill="#EA4335"
    />
  </svg>
);

const MicrosoftIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
    <rect x="1" y="1" width="8.5" height="8.5" fill="#F25022" />
    <rect x="10.5" y="1" width="8.5" height="8.5" fill="#7FBA00" />
    <rect x="1" y="10.5" width="8.5" height="8.5" fill="#00A4EF" />
    <rect x="10.5" y="10.5" width="8.5" height="8.5" fill="#FFB900" />
  </svg>
);

const icons: Record<OAuthProvider, () => JSX.Element> = {
  google: GoogleIcon,
  microsoft: MicrosoftIcon,
};

export function SocialButton({ provider, label, onClick }: SocialButtonProps) {
  const Icon = icons[provider];
  return (
    <Button
      type="button"
      variant="outline"
      className="w-full h-12 gap-3 text-sm font-medium"
      onClick={onClick}
    >
      <Icon />
      {label}
    </Button>
  );
}
