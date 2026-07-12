import { cva, type VariantProps } from "class-variance-authority";
import { ActivityIndicator, Pressable, Text } from "react-native";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "flex-row items-center justify-center rounded-lg",
  {
    variants: {
      variant: {
        default: "bg-primary active:opacity-90",
        outline: "border border-border bg-background active:bg-muted",
        ghost: "active:bg-muted",
        destructive: "bg-destructive active:opacity-90",
      },
      size: {
        sm: "h-8 px-3",
        default: "h-10 px-4",
        lg: "h-12 px-6",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

const textVariants = cva("text-sm font-medium", {
  variants: {
    variant: {
      default: "text-primary-foreground",
      outline: "text-foreground",
      ghost: "text-foreground",
      destructive: "text-primary-foreground",
    },
  },
  defaultVariants: { variant: "default" },
});

type ButtonProps = React.ComponentProps<typeof Pressable> &
  VariantProps<typeof buttonVariants> & {
    children: React.ReactNode;
    loading?: boolean;
  };

export function Button({
  variant,
  size,
  loading,
  children,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <Pressable
      className={cn(
        buttonVariants({ variant, size }),
        disabled && "opacity-50",
        className as string | undefined
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <ActivityIndicator size="small" color={variant === "default" || variant === "destructive" ? "#ffffff" : "#1a1510"} />
      ) : typeof children === "string" ? (
        <Text className={textVariants({ variant })}>{children}</Text>
      ) : (
        children
      )}
    </Pressable>
  );
}
