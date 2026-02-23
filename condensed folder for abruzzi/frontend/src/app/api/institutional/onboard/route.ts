import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { name, email, organization, volume, address } = body;

    if (!name || !email || !organization || !volume) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }

    // In a production environment, this would:
    // 1. Store the lead in a database (e.g., Postgres)
    // 2. Send an automated email to the founder
    // 3. Trigger a Slack/Discord notification
    
    console.log(`Institutional Lead Captured: ${name} from ${organization} (${volume})`);

    // Simulate automated whitelisting request for the Genesis Vault
    // In production, this would be handled by the admin after verification
    const genesisVault = "0x74481b2E0344E97C86f2ab64BB221380733C5CD0";
    console.log(`Whitelisting Request Queued for Vault: ${genesisVault} | Address: ${address || 'N/A'}`);

    return NextResponse.json({ 
      success: true, 
      message: 'Application received. Our institutional desk will contact you within 24 hours.' 
    });
  } catch (e) {
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
