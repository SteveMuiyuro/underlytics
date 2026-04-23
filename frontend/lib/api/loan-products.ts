import { ApiLoanProduct } from "@/lib/types/api-loan-product";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function getLoanProducts(): Promise<ApiLoanProduct[]> {
  const response = await fetch(`${API_URL}/api/loan-products`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch loan products");
  }

  return response.json();
}