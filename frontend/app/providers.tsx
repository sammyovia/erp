'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { LayoutWrapper } from '@/components/layout/LayoutWrapper';
import { usePathname } from 'next/navigation';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
});

export function Providers({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname === '/login' || pathname === '/register';

  return (
    <QueryClientProvider client={queryClient}>
      {isAuthPage ? children : <LayoutWrapper>{children}</LayoutWrapper>}
    </QueryClientProvider>
  );
}