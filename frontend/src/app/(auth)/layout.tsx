// Auth layout - no sidebar for sign-in/sign-up pages
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
