import ProtectedRoute from "@/components/ProtectedRoute";

export default function PedidoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ProtectedRoute allowedRoles={["user"]}>{children}</ProtectedRoute>;
}
