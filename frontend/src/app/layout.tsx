import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "sonner";

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "KERNE | The Yield-Bearing Stablecoin Ecosystem",
  description: "Institutional-grade delta-neutral assets on Base. 100% Transparent. 100% On-Chain.",
  openGraph: {
    title: "KERNE | The Yield-Bearing Stablecoin Ecosystem",
    description: "Institutional-grade delta-neutral assets on Base. 100% Transparent. 100% On-Chain.",
    url: "https://kerne.finance",
    siteName: "Kerne Protocol",
    images: [
      {
        url: "https://kerne.finance/terminal-preview.png",
        width: 1200,
        height: 630,
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "KERNE | The Yield-Bearing Stablecoin Ecosystem",
    description: "Institutional-grade delta-neutral assets on Base. 100% Transparent. 100% On-Chain.",
    creator: "@KerneProtocol",
    images: ["https://kerne.finance/terminal-preview.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${jetbrainsMono.variable} font-mono antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          forcedTheme="dark"
          enableSystem={false}
          disableTransitionOnChange
        >
          <Providers>
            {children}
            <Toaster 
              theme="dark" 
              position="bottom-right" 
              toastOptions={{
                className: "font-mono uppercase text-[10px] tracking-widest border-emerald-500/20 bg-obsidian text-emerald-500",
              }}
            />
          </Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}
