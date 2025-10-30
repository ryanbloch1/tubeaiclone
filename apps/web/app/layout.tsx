import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { ToastProvider } from "@/components/providers/ToastProvider";
import Navbar from "@/components/navigation/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TubeAI Clone",
  description: "Generate video scripts and voiceovers with AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-slate-50 text-slate-900 min-h-screen antialiased`}>
        <AuthProvider>
          <ToastProvider>
            <Navbar />
            <main className="min-h-screen">
              {children}
            </main>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
