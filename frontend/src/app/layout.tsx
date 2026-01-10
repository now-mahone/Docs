import type { Metadata } from "next";
import { Space_Grotesk, Manrope } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "sonner";
import { AccessGate } from "@/components/AccessGate";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
});

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-sans",
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
      <body className={`${spaceGrotesk.variable} ${manrope.variable} font-sans antialiased bg-white text-zinc-900 selection:bg-primary/20`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem={false}
          forcedTheme="light"
          disableTransitionOnChange
        >
          <AccessGate>
            <Providers>
              {children}
              <Toaster 
                theme="light" 
              position="bottom-right" 
              toastOptions={{
                className: "font-sans uppercase text-[10px] tracking-widest border-zinc-200 bg-white text-zinc-900 shadow-xl",
              }}
              />
            </Providers>
          </AccessGate>
        </ThemeProvider>
      </body>
    </html>
  );
}
