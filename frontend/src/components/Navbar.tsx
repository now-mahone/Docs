// Created: 2026-01-28
'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

function NavButton({ href, children, icon: Icon, className = "" }: { href: string; children: React.ReactNode; icon?: React.ElementType; className?: string }) {
  return (
    <Link href={href} className={`relative px-6 bg-[#000000] text-[#ffffff] text-s font-bold rounded-sm hover:bg-[#000000] transition-all border-none outline-none h-12 gap-2 flex items-center justify-center ${className}`}>
      {children}
      {Icon && <Icon size={16} />}
    </Link>
  );
}

export default function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { name: 'About', href: '/about' },
    { name: 'Transparency', href: '/transparency' },
    { name: 'Documentation', href: 'https://docs.kerne.ai' },
  ].filter(link => {
    if (pathname === '/terminal' && link.name === 'Documentation') {
      return false;
    }
    return true;
  });

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  return (
    <>
    <motion.nav 
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      className="fixed top-6 left-0 right-0 z-[100]"
    >
      <div className="max-w-[1920px] mx-auto px-6 md:px-12">
        {/* Floating bar with perfect symmetry: 16px (px-4) horizontal and 16px vertical spacing for internal elements */}
        <div className="h-20 border border-[#aab9be] bg-[#ffffff]/80 backdrop-blur-md rounded-sm shadow-sm px-4 flex items-center justify-between">
          <div className="flex justify-start items-center">
            <Link href="/" className="flex items-center">
              <img 
                src="/kerne-lockup.svg" 
                alt="Kerne" 
                style={{ width: '95px', height: '20px' }} 
              />
            </Link>
          </div>
          
          <div className="hidden lg:flex flex-1 justify-end items-center gap-12 text-s font-bold tracking-tight text-[#000000] mr-12 ml-12">
            {navLinks.map((link) => 
              link.href.startsWith('http') ? (
                <a 
                  key={link.href}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="transition-colors text-s hover:text-[#000000]"
                >
                  {link.name}
                </a>
              ) : (
                <Link 
                  key={link.href}
                  href={link.href} 
                  className={`transition-colors text-s ${pathname === link.href ? 'text-[#000000]' : 'hover:text-[#000000]'}`}
                >
                  {link.name}
                </Link>
              )
            )}
          </div>

          <div className="flex justify-end items-center gap-3">
            <a href="/terminal" target="_blank" rel="noopener noreferrer" className="relative px-6 bg-[#000000] text-[#ffffff] text-s font-bold rounded-sm hover:bg-[#000000] transition-all border-none outline-none h-12 gap-2 items-center justify-center hidden sm:flex">
              Launch Terminal
              <LayoutDashboard size={16} />
            </a>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden flex items-center justify-center w-12 h-12 bg-[#000000] text-[#ffffff] rounded-sm hover:bg-[#1a1a1a] transition-all"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </div>
    </motion.nav>

    {/* Mobile Menu Overlay */}
    <AnimatePresence>
      {mobileMenuOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-[#000000]/20 backdrop-blur-sm z-[90] lg:hidden"
            onClick={closeMobileMenu}
          />

          {/* Mobile Menu */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="fixed top-32 left-0 right-0 z-[95] lg:hidden"
          >
            <div className="max-w-[1920px] mx-auto px-6 md:px-12">
              <div className="bg-[#ffffff]/80 backdrop-blur-md border border-[#aab9be] rounded-sm overflow-hidden px-4">
                {/* Navigation Links */}
                <div className="flex flex-col">
                  {navLinks.map((link, index) => 
                    link.href.startsWith('http') ? (
                      <a
                        key={link.href}
                        href={link.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={closeMobileMenu}
                        className={`py-4 text-s font-bold transition-colors text-[#000000] hover:bg-[#f5f5f5] ${index !== navLinks.length - 1 ? 'border-b border-[#aab9be]' : ''}`}
                      >
                        {link.name}
                      </a>
                    ) : (
                      <Link
                        key={link.href}
                        href={link.href}
                        onClick={closeMobileMenu}
                        className={`py-4 text-s font-bold transition-colors ${
                          pathname === link.href 
                            ? 'text-[#000000] bg-[#f5f5f5]' 
                            : 'text-[#000000] hover:bg-[#f5f5f5]'
                        } ${index !== navLinks.length - 1 ? 'border-b border-[#aab9be]' : ''}`}
                      >
                        {link.name}
                      </Link>
                    )
                  )}
                  
                  {/* Mobile Terminal Button */}
                  <div className="sm:hidden border-t border-[#aab9be] pt-4 pb-4">
                    <a
                      href="/terminal"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-6 bg-[#000000] text-[#ffffff] text-s font-bold rounded-sm hover:bg-[#1a1a1a] transition-all h-12 gap-2 flex items-center justify-center"
                      onClick={closeMobileMenu}
                    >
                      Launch Terminal
                      <LayoutDashboard size={16} />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
    </>
  );
}
