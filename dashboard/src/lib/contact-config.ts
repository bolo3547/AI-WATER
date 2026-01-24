/**
 * Public Contact Configuration
 * 
 * This file contains all public-facing contact information.
 * Update these values to match your utility's contact details.
 * 
 * For environment-based configuration, set these in your .env.local file:
 * - NEXT_PUBLIC_WHATSAPP_NUMBER
 * - NEXT_PUBLIC_USSD_CODE
 * - NEXT_PUBLIC_EMERGENCY_NUMBER
 * - NEXT_PUBLIC_SUPPORT_PHONE
 * - NEXT_PUBLIC_SUPPORT_EMAIL
 */

export const contactConfig = {
  // WhatsApp Business number for public reporting
  // Format: country code + number without spaces (e.g., "260971234567")
  whatsapp: {
    number: process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || '260971234567',
    // Formatted display version
    get display() {
      const num = this.number
      // Format: +260 97 123 4567
      if (num.length === 12 && num.startsWith('260')) {
        return `+${num.slice(0, 3)} ${num.slice(3, 5)} ${num.slice(5, 8)} ${num.slice(8)}`
      }
      return `+${num}`
    },
    // WhatsApp click-to-chat URL
    get url() {
      return `https://wa.me/${this.number}?text=${encodeURIComponent('Hi AquaWatch, I want to report a water issue.')}`
    }
  },

  // USSD short code for feature phone reporting
  ussd: {
    code: process.env.NEXT_PUBLIC_USSD_CODE || '*384*123#',
    get display() {
      return this.code
    }
  },

  // Emergency hotline (24/7 for burst mains, flooding)
  emergency: {
    number: process.env.NEXT_PUBLIC_EMERGENCY_NUMBER || '260211999000',
    get display() {
      const num = this.number
      if (num.length === 12 && num.startsWith('260')) {
        return `+${num.slice(0, 3)} ${num.slice(3, 6)} ${num.slice(6, 9)} ${num.slice(9)}`
      }
      return `+${num}`
    },
    get tel() {
      return `tel:+${this.number}`
    }
  },

  // General support line
  support: {
    phone: process.env.NEXT_PUBLIC_SUPPORT_PHONE || '260211123456',
    email: process.env.NEXT_PUBLIC_SUPPORT_EMAIL || 'support@aquawatch.io',
    get phoneDisplay() {
      const num = this.phone
      if (num.length === 12 && num.startsWith('260')) {
        return `+${num.slice(0, 3)} ${num.slice(3, 6)} ${num.slice(6, 9)} ${num.slice(9)}`
      }
      return `+${num}`
    },
    get phoneTel() {
      return `tel:+${this.phone}`
    }
  },

  // Social media (optional)
  social: {
    facebook: process.env.NEXT_PUBLIC_FACEBOOK_URL || '',
    twitter: process.env.NEXT_PUBLIC_TWITTER_URL || '',
    instagram: process.env.NEXT_PUBLIC_INSTAGRAM_URL || '',
  },

  // Organization details
  organization: {
    name: process.env.NEXT_PUBLIC_ORG_NAME || 'AquaWatch',
    fullName: process.env.NEXT_PUBLIC_ORG_FULL_NAME || 'AquaWatch NRW Detection System',
    website: process.env.NEXT_PUBLIC_ORG_WEBSITE || 'https://aquawatch.io',
  }
}

// Helper function to get all contacts as a simple object (for API responses)
export function getContactInfo() {
  return {
    whatsapp: {
      number: contactConfig.whatsapp.number,
      display: contactConfig.whatsapp.display,
      url: contactConfig.whatsapp.url,
    },
    ussd: {
      code: contactConfig.ussd.code,
    },
    emergency: {
      number: contactConfig.emergency.number,
      display: contactConfig.emergency.display,
    },
    support: {
      phone: contactConfig.support.phone,
      phoneDisplay: contactConfig.support.phoneDisplay,
      email: contactConfig.support.email,
    },
    organization: contactConfig.organization,
  }
}

export default contactConfig
