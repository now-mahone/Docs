import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { code } = await request.json();

    // In a production environment, this would check against a database or the bot's persistence layer.
    // For the Genesis Phase, we use a set of high-value master codes and a pattern check.
    const MASTER_CODES = ['KERNE-GENESIS-2026', 'WHALE-ALPHA-001', 'INSTITUTIONAL-BETA'];
    
    // Simple pattern: KERNE-XXXX where XXXX is numeric (simulating generated codes)
    const isGeneratedCode = /^KERNE-\d{4}$/.test(code);

    if (MASTER_CODES.includes(code) || isGeneratedCode) {
      const response = NextResponse.json({ success: true });
      
      // Set a secure cookie to maintain access
      response.cookies.set('kerne_access_token', 'granted_genesis_2026', {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 60 * 60 * 24 * 7, // 1 week
        path: '/',
      });

      return response;
    }

    return NextResponse.json({ success: false, message: 'Invalid Access Code' }, { status: 401 });
  } catch (error) {
    return NextResponse.json({ success: false, message: 'Server Error' }, { status: 500 });
  }
}
