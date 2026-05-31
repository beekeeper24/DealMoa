import { ProductDetailPage } from "@/details/ProductDetailPage";

export default async function ProductPage({
  params
}: {
  params: Promise<{ productId: string }>;
}) {
  const { productId } = await params;
  return <ProductDetailPage productId={productId} />;
}
