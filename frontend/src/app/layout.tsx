import type { Metadata } from "next";
import { Manrope } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "sonner";

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "KERNE | The Yield-Bearing Stablecoin Ecosystem",
  description: "Institutional grade delta neutral assets on Base. 100% Transparent. 100% On-Chain.",
  icons: {
    icon: "/favicon.svg",
  },
  metadataBase: new URL("https://kerne.ai"),
  openGraph: {
    title: "KERNE | The Yield-Bearing Stablecoin Ecosystem",
    description: "Institutional grade delta neutral assets on Base. 100% Transparent. 100% On-Chain.",
    url: "https://kerne.ai",
    siteName: "Kerne Protocol",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "KERNE Protocol",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "KERNE | The Yield-Bearing Stablecoin Ecosystem",
    description: "Institutional grade delta neutral assets on Base. 100% Transparent. 100% On-Chain.",
    creator: "@KerneProtocol",
    images: ["/og-image.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* TASA Orbiter font via Google Fonts CDN */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=TASA+Orbiter:wght@400..800&display=swap" rel="stylesheet" />
      </head>
      <body className={`${manrope.variable} font-sans antialiased bg-[#ffffff] text-[#000000] selection:bg-[#000000]/10`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem={false}
          forcedTheme="light"
          disableTransitionOnChange
        >
          <Providers>
            {children}
            <Toaster 
              theme="light" 
              position="bottom-right" 
              toastOptions={{
                className: "font-sans uppercase text-xs tracking-widest border-[#000000]/10 bg-white text-[#000000]",
              }}
            />
          </Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}
