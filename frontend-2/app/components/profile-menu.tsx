"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Settings, HelpCircle, LogOut } from "lucide-react";
import { clearToken, fetchCurrentUser } from "@/app/lib/api";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/app/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/app/components/ui/alert-dialog";

interface ProfileMenuProps {
  children: React.ReactNode;
}

export function ProfileMenu({ children }: ProfileMenuProps) {
  const router = useRouter();
  const [confirmingLogout, setConfirmingLogout] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const [minutesUsed, setMinutesUsed] = useState<number | null>(null);

  useEffect(() => {
    fetchCurrentUser()
      .then((user) => setMinutesUsed(user.minutes_used_this_month))
      .catch(() => {/* silently ignore */});
  }, []);

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await clearToken();
    } catch {
      // Even if signOut fails server-side, redirect to login
    } finally {
      router.push("/login");
    }
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger render={<button className="w-full text-left" />}>
          {children}
        </DropdownMenuTrigger>
        <DropdownMenuContent side="top" align="start" className="w-48">
          {/* Monthly usage */}
          {minutesUsed !== null && (
            <div className="px-2 py-1.5 text-xs text-muted-foreground">
              <div className="flex items-center justify-between mb-1">
                <span>Monthly usage</span>
                <span className="font-medium text-foreground">{minutesUsed} min</span>
              </div>
              <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all"
                  style={{ width: `${Math.min(100, (minutesUsed / 300) * 100)}%` }}
                />
              </div>
            </div>
          )}
          <DropdownMenuItem>
            <Settings />
            Account Settings
          </DropdownMenuItem>
          <DropdownMenuItem>
            <HelpCircle />
            Help Center
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="text-destructive focus:text-destructive"
            onClick={() => setConfirmingLogout(true)}
          >
            <LogOut />
            Logout
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <AlertDialog open={confirmingLogout} onOpenChange={setConfirmingLogout}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm logout?</AlertDialogTitle>
            <AlertDialogDescription>
              You will be redirected to the login page.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={loggingOut}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleLogout}
              disabled={loggingOut}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {loggingOut ? "Logging out..." : "Logout"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
