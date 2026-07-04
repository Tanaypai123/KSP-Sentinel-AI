import type { FIR, Accused, Notification, Alert, CourtHearing, AIInsight, Message } from './types';

export const mockFIRs: FIR[] = [
  {
    id: 'fir-1',
    caseNumber: 'FIR 402/2026',
    title: 'Syndicated Cyber Extortion & Ransomware Attack',
    underSection: 'BNS Sec 308 (Extortion) & IT Act Sec 66D',
    status: 'Investigation',
    dateRegistered: '2026-06-28',
    complainant: 'Narayana Health Systems CIO',
    details: 'Ransomware deployment on hospital servers resulting in operational shutdown. Attackers demanded 45 BTC. Digital forensics traced entry vector to a compromised vendor VPN.',
    summary: 'Ransomware deployment on health infrastructure. Attacker group: "Gowda_Net". Digital trail points to local proxy nodes in Bengaluru.',
    officersAssigned: ['Inspector Vikram Rathore', 'SI Ananya Hegde'],
    location: 'Cyber Crime PS, Bengaluru City',
    severity: 'Critical'
  },
  {
    id: 'fir-2',
    caseNumber: 'FIR 289/2026',
    title: 'High-Value Commercial Burglary & Safe Cracking',
    underSection: 'BNS Sec 331 (House-trespass) & Sec 305 (Theft)',
    status: 'Open',
    dateRegistered: '2026-07-01',
    complainant: 'Sri Krishna Jewellers Manager',
    details: 'Unauthorized entry through rear ventilator shaft. Locker opened using sophisticated thermal lance. 12.4kg gold ornaments and diamonds missing. CCTV footage disabled manually at the circuit breaker.',
    summary: 'Theft of gold ornaments worth ₹7.5 Crore from safe. Suspect group active in South Bengaluru. Likely inside assistance.',
    officersAssigned: ['Inspector Vikram Rathore', 'SI Mahesh K.'],
    location: 'Jayanagar PS, Bengaluru',
    severity: 'High'
  },
  {
    id: 'fir-3',
    caseNumber: 'FIR 156/2026',
    title: 'Inter-State Synthetic Drug Trafficking Ring',
    underSection: 'NDPS Act Section 20 & 22',
    status: 'Investigation',
    dateRegistered: '2026-06-15',
    complainant: 'KSP Intelligence Wing (Sua Sponte)',
    details: 'Intelligence led raid at a warehouse near Electronic City. Seized 4.2 kg MDMA crystals, packaging materials, and synthetic precursors. Distribution network operating via encrypted messaging apps.',
    summary: 'Synthetic drug distribution hub busted in Electronic City. Link established with Goa and Mumbai suppliers.',
    officersAssigned: ['Inspector Vikram Rathore', 'ACP H. R. Patil'],
    location: 'Electronic City PS, Bengaluru',
    severity: 'High'
  },
  {
    id: 'fir-4',
    caseNumber: 'FIR 310/2026',
    title: 'Corporate Financial Fraud & Money Laundering',
    underSection: 'BNS Sec 318 (Cheating) & PMLA Sec 3',
    status: 'Under Review',
    dateRegistered: '2026-07-03',
    complainant: 'Directorate of Enforcement (ED) Liaison',
    details: 'Shell company shell network detected funneling funds from real estate developments into offshore shell accounts. Discrepancies found in auditing registers of Apex Realty Group.',
    summary: 'Diversion of ₹140 Crore in public booking funds to Singapore bank accounts via shell directors.',
    officersAssigned: ['SI Ananya Hegde'],
    location: 'Koramangala PS, Bengaluru',
    severity: 'Medium'
  },
  {
    id: 'fir-5',
    caseNumber: 'FIR 98/2026',
    title: 'Assault & Weaponized Riotous Mob Violence',
    underSection: 'BNS Sec 191 (Riot) & Sec 115 (Voluntary hurt)',
    status: 'Closed',
    dateRegistered: '2026-05-12',
    complainant: 'Public Property Custodian',
    details: 'Clashes between two local political factions during a rally. Damage to public buses and private vehicles. Multiple civilian casualties reported with minor injuries.',
    summary: 'Factional rioting in Shivaji Nagar. 14 suspects detained, processed, and chargesheets filed. Case closed after court sentencing.',
    officersAssigned: ['SI Mahesh K.'],
    location: 'Shivaji Nagar PS, Bengaluru',
    severity: 'Medium'
  }
];

export const mockAccused: Accused[] = [
  {
    id: 'acc-1',
    name: 'Rajesh "Gowda" Gowda',
    age: 34,
    photoSeed: 'rajesh',
    status: 'At Large',
    riskScore: 92,
    biometricsMatch: 87.5,
    primaryOffense: 'Ransomware deployment & Crypto Launderer',
    notes: 'Operates dark web syndicate "Gowda_Net". Expert in network intrusion and cryptocurrency tumbling. Believed to be hiding in rural borders between Karnataka and Andhra Pradesh.',
    networkConnections: ['FIR 402/2026', 'Vikram "Techie" Rao', 'Karthik Hegde', 'Apex Realty Group'],
    lastKnownLocation: 'Madanapalle Border Area',
    phoneNumbers: ['+91-98450-11223', '+91-88670-34543'],
    associates: ['Vikram "Techie" Rao', 'Karan Shetty']
  },
  {
    id: 'acc-2',
    name: 'Vikram "Techie" Rao',
    age: 29,
    photoSeed: 'vikram',
    status: 'In Custody',
    riskScore: 78,
    biometricsMatch: 99.1,
    primaryOffense: 'System Intrusion & Initial Access Brokerage',
    notes: 'Former systems administrator. Arrested on 2026-06-30 near Kempegowda Airport. Confessed to selling VPN credentials of Narayana Health Systems to Rajesh Gowda.',
    networkConnections: ['FIR 402/2026', 'Rajesh "Gowda" Gowda'],
    lastKnownLocation: 'Parappana Agrahara Central Prison, Bengaluru',
    phoneNumbers: ['+91-94480-45621'],
    associates: ['Rajesh "Gowda" Gowda']
  },
  {
    id: 'acc-3',
    name: 'Munna "Safe-Cracker" Qureshi',
    age: 41,
    photoSeed: 'munna',
    status: 'At Large',
    riskScore: 85,
    biometricsMatch: 64.2,
    primaryOffense: 'Safe-Breaking & Gas Torch Operations',
    notes: 'Known inter-state safe specialist. MODUS OPERANDI: Safe penetration using thermal lances/gas cutting. Active in Maharashtra, Goa, and Karnataka.',
    networkConnections: ['FIR 289/2026', 'Jayanagar Jewellers Robbery'],
    lastKnownLocation: 'Hubballi Transit Point',
    phoneNumbers: ['+91-97310-99881', '+91-91080-87723'],
    associates: ['Sanjay Deshmukh', 'Yusuf Safeer']
  },
  {
    id: 'acc-4',
    name: 'Elena Rostova',
    age: 32,
    photoSeed: 'elena',
    status: 'Under Trial',
    riskScore: 68,
    biometricsMatch: 95.8,
    primaryOffense: 'Synthetic Drug Manufacturing & Logistics',
    notes: 'Foreign national residing in India on expired visa. Identified as the lead chemist for the Electronic City warehouse drug lab.',
    networkConnections: ['FIR 156/2026', 'Goa-Cargo Transit Link'],
    lastKnownLocation: 'Women Custody Facility, Bengaluru',
    phoneNumbers: ['+91-88840-00912'],
    associates: ['Suresh Nair', 'Aditya Sen']
  }
];

export const mockNotifications: Notification[] = [
  {
    id: 'n-1',
    text: 'Threat intel update: Active C2 server of "Gowda_Net" spotted originating from AP border IP range.',
    time: '4 mins ago',
    severity: 'critical',
    unread: true
  },
  {
    id: 'n-2',
    text: 'Munna Qureshi\'s burner phone pinged a tower near Hubballi Toll Plaza 15 minutes ago.',
    time: '15 mins ago',
    severity: 'warning',
    unread: true
  },
  {
    id: 'n-3',
    text: 'Forensic Lab submitted final report for Jayanagar safe cracking fingerprints.',
    time: '2 hours ago',
    severity: 'info',
    unread: false
  },
  {
    id: 'n-4',
    text: 'High Court schedule updated for Case FIR 156/2026 (Elena Rostova Bail hearing).',
    time: '5 hours ago',
    severity: 'info',
    unread: false
  }
];

export const mockAlerts: Alert[] = [
  {
    id: 'al-1',
    type: 'CRITICAL',
    text: 'SUSPECT TRACKING: Munna Qureshi cell phone pinged Hubballi tower.',
    timestamp: '14:10:45',
    location: 'Hubballi'
  },
  {
    id: 'al-2',
    type: 'WARNING',
    text: 'CYBER EXTRAPOLATION: Port scan spike detected against state power grid servers.',
    timestamp: '13:45:12',
    location: 'State Data Center'
  },
  {
    id: 'al-3',
    type: 'INFO',
    text: 'SYSTEM STATUS: AI Sentinel Model re-indexing complete (99.8% accuracy).',
    timestamp: '12:00:00'
  }
];

export const mockCourtHearings: CourtHearing[] = [
  {
    id: 'ch-1',
    caseNumber: 'FIR 156/2026',
    accusedName: 'Elena Rostova',
    courtName: 'Karnataka High Court - Court Hall 3',
    hearingDate: '2026-07-06 10:30 AM',
    bench: 'Justice G. R. Venkatraman',
    status: 'Scheduled'
  },
  {
    id: 'ch-2',
    caseNumber: 'FIR 402/2026',
    accusedName: 'Vikram "Techie" Rao',
    courtName: 'Special Cyber Crime Court',
    hearingDate: '2026-07-08 02:00 PM',
    bench: 'Sessions Judge M. Basavaraju',
    status: 'Scheduled'
  },
  {
    id: 'ch-3',
    caseNumber: 'FIR 98/2026',
    accusedName: 'Shivaji Nagar Mob Riot Suspects (14)',
    courtName: 'Fast Track Sessions Court 4',
    hearingDate: '2026-07-04 11:30 AM',
    bench: 'Judge Sandhya Reddy',
    status: 'Completed'
  }
];

export const mockAIInsights: AIInsight[] = [
  {
    id: 'ins-1',
    title: 'Cross-Case Financial Signature Detected',
    description: 'Crypto wallet address (0x74a...81) linked to Rajesh Gowda\'s extortion ransom has received two transactions of ₹5 Lakh each from an offshore shell director linked to the Apex Realty Group fraud (FIR 310/2026). Suggests Rajesh Gowda may be laundering real estate diversion profits or executing corporate extortion.',
    confidence: 94,
    tags: ['Crypto Laundering', 'Cyber Crime', 'Financial Fraud']
  },
  {
    id: 'ins-2',
    title: 'Modus Operandi Shift: Gas Lance Attacks',
    description: 'Safe cracking event in Jayanagar (FIR 289) shares 92% fingerprint, metallurgical cutting residue, and tactical entry timings with 3 unsolved cases in Pune and Margao. Munna Qureshi is the primary common denominating suspect.',
    confidence: 88,
    tags: ['Safe Cracking', 'Burglary', 'SOP Profile']
  },
  {
    id: 'ins-3',
    title: 'Geographic Clustering Alert',
    description: 'Synthetic drug distribution (Electronic City) and commercial safe cracking (Jayanagar) display dense cell tower overlaps. 4 burner phones have been detected traversing both zones in less than 3 hours.',
    confidence: 76,
    tags: ['Geographic Linkage', 'NDPS']
  }
];

export const mockSuggestedQueries = [
  'Analyze connections for accused Rajesh "Gowda" Gowda',
  'Summarize FIR 402/2026 ransomware attack details',
  'Show active cell tower pings for suspect Munna Qureshi',
  'What is the correlation between Apex Realty Group and Gowda_Net?'
];

export const mockRecentSearches = [
  'FIR 402/2026',
  'Munna Qureshi tracker',
  'Cyber Crime PS cases',
  'Apex Realty accounts'
];

// Pre-computed chatbot responses matching queries to show off Palantir-like intelligence operations
export const getAIResponse = (query: string): Message => {
  const normalized = query.toLowerCase().trim();

  if (normalized.includes('rajesh') || normalized.includes('gowda')) {
    return {
      id: `ai-res-${Date.now()}`,
      sender: 'assistant',
      text: 'Cross-analyzing dossier for Rajesh "Gowda" Gowda against active intelligence indexes. I have identified 4 primary linkages: a critical link to the hospital ransomware attack (FIR 402/2026), suspicious financial interactions with Apex Realty Group, and active geolocation tracking in the Andhra border region.',
      timestamp: new Date().toLocaleTimeString(),
      structuredAnswer: {
        summary: 'Target Rajesh Gowda is the primary operator of "Gowda_Net" cyber syndicate. Forensic audits reveal financial laundering links to Apex Realty Group directors.',
        timeline: [
          { time: '2026-06-28', event: 'Narayana Health hospital systems compromised. Ransom note signed "G_Net".', status: 'COMPLETED' },
          { time: '2026-06-30', event: 'Associate Vikram "Techie" Rao arrested. Confesses to supplying access credentials.', status: 'COMPLETED' },
          { time: '2026-07-02', event: 'Gowda_Net wallet (0x74a...) receives 0.8 BTC tumbler transfers.', status: 'LOGGED' },
          { time: '2026-07-04', event: 'Cell ping detects transit near Madanapalle border.', status: 'ACTIVE TRACKING' }
        ],
        entities: [
          { name: 'Rajesh "Gowda" Gowda', type: 'Suspect (At Large)', details: 'Syndicate Kingpin. Risk Index 92%', risk: 'High' },
          { name: 'Vikram "Techie" Rao', type: 'Co-conspirator (In Custody)', details: 'VPN Credentials provider', risk: 'Medium' },
          { name: 'Apex Realty Group', type: 'Financial Link', details: 'Funneled ₹10 Lakhs through shell entities', risk: 'High' }
        ],
        recommendedActions: [
          'Issue Look Out Circular (LOC) at Kempegowda Airport and Chennai International Airport.',
          'Execute freezing order under PMLA Sec 5 on wallet 0x74a...81.',
          'Dispatch Border Patrol intercept team to Madanapalle cellular grid sector B4.'
        ],
        jsonPayload: JSON.stringify({
          entity: "Rajesh Gowda",
          status: "Wanted",
          cases_linked: ["FIR-402/2026", "FIR-310/2026"],
          last_cell_tower: "Madanapalle Sector B4",
          threat_level: "Critical (92)"
        }, null, 2)
      }
    };
  }

  if (normalized.includes('402/2026') || normalized.includes('ransomware') || normalized.includes('narayana')) {
    return {
      id: `ai-res-${Date.now()}`,
      sender: 'assistant',
      text: 'Retrieved FIR 402/2026 details. This involves the Narayana Health Systems ransomware compromise. Attacker group used compromised vendor VPN credentials to move laterally and encrypt primary active directories. Recommending immediate forensic segregation.',
      timestamp: new Date().toLocaleTimeString(),
      structuredAnswer: {
        summary: 'FIR 402/2026. Attack Vector: Compomised Citrix Gateway of vendor "Aegis Medtech". Impact: 800+ nodes encrypted. Ransom requested: 45 BTC.',
        timeline: [
          { time: '04:12 AM', event: 'Initial access established via vendor credentials.', status: 'DETECTION' },
          { time: '05:30 AM', event: 'Lateral movement and Active Directory takeover.', status: 'COMPLETED' },
          { time: '06:15 AM', event: 'Ransomware deployment. Critical database lockout.', status: 'CRITICAL' },
          { time: '11:00 AM', event: 'FIR filed by Narayana Health Group Chief Security Officer.', status: 'ACTIONED' }
        ],
        entities: [
          { name: 'Narayana Health Systems', type: 'Victim', details: 'Critical Hospital Infrastructure', risk: 'Low' },
          { name: 'Aegis Medtech', type: 'Compromised Vendor', details: 'VPN breach entry point', risk: 'Medium' },
          { name: 'Gowda_Net', type: 'Attacker Syndicate', details: 'Demanded 45 BTC payment', risk: 'High' }
        ],
        recommendedActions: [
          'Isolate Aegis Medtech VPN tunnel instantly.',
          'Deploy KSP Forensic recovery scripts to retrieve system log dumps.',
          'Cross-reference forensic MAC addresses with Vikram Rao\'s confiscated laptops.'
        ],
        jsonPayload: JSON.stringify({
          case: "FIR 402/2026",
          victim: "Narayana Health Systems",
          intrusion_vector: "Compromised Citrix VPN",
          indicators_of_compromise: ["103.88.92.12", "narayana_db_lockout.bin"],
          remediation_status: "Active Isolation"
        }, null, 2)
      }
    };
  }

  if (normalized.includes('munna') || normalized.includes('qureshi') || normalized.includes('tower')) {
    return {
      id: `ai-res-${Date.now()}`,
      sender: 'assistant',
      text: 'Extracting live surveillance and triangulation files for Munna "Safe-Cracker" Qureshi. Cellular intercept logs registered tower pings in Hubballi, Karnataka. Tactical teams in Hubballi City have been briefed.',
      timestamp: new Date().toLocaleTimeString(),
      structuredAnswer: {
        summary: 'Target Munna Qureshi is active. Registered a cellular handoff on Karnataka Highway NH-48 traveling northbound towards Belagavi/Maharashtra border.',
        timeline: [
          { time: '12:15 PM', event: 'Handset power-on registered in Davanagere.', status: 'LOGGED' },
          { time: '02:10 PM', event: 'Cell tower ping at Hubballi Toll Plaza. Handset active 42 seconds.', status: 'ACTIVE' },
          { time: '02:40 PM', event: 'Burner SIM registration lookup indicates fake ID (Aadhaar named Ramesh Kumar).', status: 'FLAGGED' }
        ],
        entities: [
          { name: 'Munna "Safe-Cracker" Qureshi', type: 'Suspect', details: 'Wanted in Jayanagar safe theft', risk: 'High' },
          { name: 'Ramesh Kumar (Fake Identity)', type: 'Alias Registry', details: 'Aadhaar photo mismatch detected', risk: 'Medium' },
          { name: 'Hubballi Toll Plaza', type: 'Transit Node', details: 'Highway CCTV captured Silver Mahindra Bolero', risk: 'Medium' }
        ],
        recommendedActions: [
          'Alert Belagavi Border checkpoint to intercept Silver Mahindra Bolero (KA-25-M-4820).',
          'Deploy localized digital IMSI Catcher scan near Hubballi Railway station (suspected alternative transit).',
          'Notify Maharashtra Police Safe-breaking cell of target heading towards Pune.'
        ]
      }
    };
  }

  if (normalized.includes('apex') || normalized.includes('realty') || normalized.includes('laud')) {
    return {
      id: `ai-res-${Date.now()}`,
      sender: 'assistant',
      text: 'Initiating forensic ledger review of Apex Realty Group. Transaction audit logs show high-frequency transfers of ₹10 Lakhs each to dummy shells. Ledger entries show direct digital currency exchange wallets operating in Andhra Pradesh.',
      timestamp: new Date().toLocaleTimeString(),
      structuredAnswer: {
        summary: 'FIR 310/2026. Money Laundering & Booking Diversion. Financial analysis reveals that 12% of diverted booking funds were converted to Bitcoin and routed to Gowda_Net operators.',
        timeline: [
          { time: '2026-03-10', event: 'First shell corporate setup (Vanguard Builders Bangalore).', status: 'COMPLETED' },
          { time: '2026-05-15', event: '₹140 Crore public investments routed to Vanguard bank accounts.', status: 'COMPLETED' },
          { time: '2026-06-25', event: 'Vanguard buys ₹10 Lakh crypto vouchers via unregulated broker.', status: 'FLAGGED' }
        ],
        entities: [
          { name: 'Apex Realty Group', type: 'Corporate Suspect', details: 'Fraudulent housing developers', risk: 'High' },
          { name: 'Vanguard Builders', type: 'Shell Company', details: 'Laundering conduit', risk: 'High' },
          { name: 'Gowda_Net Wallet', type: 'Destination Wallet', details: '0x74a...81 digital cache', risk: 'High' }
        ],
        recommendedActions: [
          'Summon CFO of Apex Realty for interrogation under PMLA Section 50.',
          'Request freeze of Vanguard Builders bank accounts at SBI Koramangala branch.',
          'Cross-match corporate email server IP logs with Rajesh Gowda\'s residence.'
        ]
      }
    };
  }

  // General query answer fallback
  return {
    id: `ai-res-${Date.now()}`,
    sender: 'assistant',
    text: `Analyzing: "${query}". I have checked the Sentinel KSP Intelligence Index. Currently, no active alerts correspond to that direct name, but there is active correlation. Here is the KSP AI analysis:`,
    timestamp: new Date().toLocaleTimeString(),
    structuredAnswer: {
      summary: `Standard search query parsed for "${query}". KSP Sentinel AI has searched active records, FIR database, court logs, and geo-data.`,
      recommendedActions: [
        'Perform a deeper network analysis to detect sub-surface links.',
        'Filter search query by specific location like Jayanagar, Koramangala, or Electronic City.',
        'Request biometric or facial identification indexing from active databases.'
      ]
    }
  };
};
