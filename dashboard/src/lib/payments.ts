// Payment Gateway Integration for Zambia
// Supports MTN Mobile Money, Airtel Money, and Card payments

export interface PaymentRequest {
  amount: number
  currency: 'ZMW'
  accountNumber: string
  customerName: string
  customerPhone: string
  description?: string
  reference?: string
  dma: string
}

export interface PaymentResponse {
  success: boolean
  transactionId?: string
  reference?: string
  status: 'pending' | 'completed' | 'failed'
  message: string
  provider?: string
}

// MTN Mobile Money Configuration
const MTN_CONFIG = {
  apiUrl: process.env.MTN_MOMO_API_URL || 'https://sandbox.momodeveloper.mtn.com',
  subscriptionKey: process.env.MTN_MOMO_SUBSCRIPTION_KEY || '',
  apiUser: process.env.MTN_MOMO_API_USER || '',
  apiKey: process.env.MTN_MOMO_API_KEY || '',
  environment: process.env.MTN_MOMO_ENVIRONMENT || 'sandbox',
  callbackUrl: process.env.NEXT_PUBLIC_APP_URL + '/api/payments/callback/mtn'
}

// Airtel Money Configuration
const AIRTEL_CONFIG = {
  apiUrl: process.env.AIRTEL_MONEY_API_URL || 'https://openapiuat.airtel.africa',
  clientId: process.env.AIRTEL_MONEY_CLIENT_ID || '',
  clientSecret: process.env.AIRTEL_MONEY_CLIENT_SECRET || '',
  callbackUrl: process.env.NEXT_PUBLIC_APP_URL + '/api/payments/callback/airtel'
}

// Check if payment providers are configured
export const paymentProviders = {
  mtn: !!(MTN_CONFIG.subscriptionKey && MTN_CONFIG.apiUser),
  airtel: !!(AIRTEL_CONFIG.clientId && AIRTEL_CONFIG.clientSecret),
  card: false // Enable when Stripe/Flutterwave is configured
}

// MTN Mobile Money
export const mtnMobileMoney = {
  async requestPayment(request: PaymentRequest): Promise<PaymentResponse> {
    if (!paymentProviders.mtn) {
      return {
        success: false,
        status: 'failed',
        message: 'MTN Mobile Money not configured. Add MTN_MOMO_* environment variables.'
      }
    }

    try {
      // Get access token
      const tokenResponse = await fetch(`${MTN_CONFIG.apiUrl}/collection/token/`, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${Buffer.from(`${MTN_CONFIG.apiUser}:${MTN_CONFIG.apiKey}`).toString('base64')}`,
          'Ocp-Apim-Subscription-Key': MTN_CONFIG.subscriptionKey
        }
      })
      
      if (!tokenResponse.ok) {
        throw new Error('Failed to get MTN access token')
      }
      
      const { access_token } = await tokenResponse.json()
      
      // Request payment
      const externalId = `LWSC-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      
      const paymentResponse = await fetch(`${MTN_CONFIG.apiUrl}/collection/v1_0/requesttopay`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${access_token}`,
          'X-Reference-Id': externalId,
          'X-Target-Environment': MTN_CONFIG.environment,
          'Ocp-Apim-Subscription-Key': MTN_CONFIG.subscriptionKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          amount: request.amount.toString(),
          currency: request.currency,
          externalId,
          payer: {
            partyIdType: 'MSISDN',
            partyId: request.customerPhone.replace('+', '')
          },
          payerMessage: `LWSC Water Bill Payment - ${request.accountNumber}`,
          payeeNote: request.description || 'Water bill payment'
        })
      })
      
      if (paymentResponse.status === 202) {
        return {
          success: true,
          transactionId: externalId,
          reference: externalId,
          status: 'pending',
          message: 'Payment request sent. Customer will receive prompt on their phone.',
          provider: 'MTN Mobile Money'
        }
      } else {
        throw new Error('Payment request failed')
      }
    } catch (error: any) {
      return {
        success: false,
        status: 'failed',
        message: error.message || 'MTN payment request failed'
      }
    }
  },
  
  async checkStatus(transactionId: string): Promise<PaymentResponse> {
    if (!paymentProviders.mtn) {
      return { success: false, status: 'failed', message: 'MTN not configured' }
    }
    
    try {
      const tokenResponse = await fetch(`${MTN_CONFIG.apiUrl}/collection/token/`, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${Buffer.from(`${MTN_CONFIG.apiUser}:${MTN_CONFIG.apiKey}`).toString('base64')}`,
          'Ocp-Apim-Subscription-Key': MTN_CONFIG.subscriptionKey
        }
      })
      
      const { access_token } = await tokenResponse.json()
      
      const statusResponse = await fetch(
        `${MTN_CONFIG.apiUrl}/collection/v1_0/requesttopay/${transactionId}`,
        {
          headers: {
            'Authorization': `Bearer ${access_token}`,
            'X-Target-Environment': MTN_CONFIG.environment,
            'Ocp-Apim-Subscription-Key': MTN_CONFIG.subscriptionKey
          }
        }
      )
      
      const data = await statusResponse.json()
      
      return {
        success: data.status === 'SUCCESSFUL',
        transactionId,
        status: data.status === 'SUCCESSFUL' ? 'completed' : 
                data.status === 'PENDING' ? 'pending' : 'failed',
        message: data.reason || `Payment ${data.status.toLowerCase()}`,
        provider: 'MTN Mobile Money'
      }
    } catch (error: any) {
      return { success: false, status: 'failed', message: error.message }
    }
  }
}

// Airtel Money
export const airtelMoney = {
  async getToken(): Promise<string | null> {
    try {
      const response = await fetch(`${AIRTEL_CONFIG.apiUrl}/auth/oauth2/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          client_id: AIRTEL_CONFIG.clientId,
          client_secret: AIRTEL_CONFIG.clientSecret,
          grant_type: 'client_credentials'
        })
      })
      
      const data = await response.json()
      return data.access_token || null
    } catch {
      return null
    }
  },
  
  async requestPayment(request: PaymentRequest): Promise<PaymentResponse> {
    if (!paymentProviders.airtel) {
      return {
        success: false,
        status: 'failed',
        message: 'Airtel Money not configured. Add AIRTEL_MONEY_* environment variables.'
      }
    }

    try {
      const token = await this.getToken()
      if (!token) throw new Error('Failed to get Airtel access token')
      
      const reference = `LWSC-${Date.now()}`
      
      const response = await fetch(`${AIRTEL_CONFIG.apiUrl}/merchant/v1/payments/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'X-Country': 'ZM',
          'X-Currency': 'ZMW'
        },
        body: JSON.stringify({
          reference,
          subscriber: {
            country: 'ZM',
            currency: 'ZMW',
            msisdn: request.customerPhone.replace('+260', '')
          },
          transaction: {
            amount: request.amount,
            country: 'ZM',
            currency: 'ZMW',
            id: reference
          }
        })
      })
      
      const data = await response.json()
      
      if (data.status?.success) {
        return {
          success: true,
          transactionId: data.data?.transaction?.id || reference,
          reference,
          status: 'pending',
          message: 'Payment request sent to customer phone.',
          provider: 'Airtel Money'
        }
      } else {
        throw new Error(data.status?.message || 'Payment failed')
      }
    } catch (error: any) {
      return {
        success: false,
        status: 'failed',
        message: error.message || 'Airtel payment request failed'
      }
    }
  }
}

// Unified Payment Handler
export async function processPayment(
  method: 'mtn_mobile_money' | 'airtel_money' | 'card' | 'cash',
  request: PaymentRequest
): Promise<PaymentResponse> {
  switch (method) {
    case 'mtn_mobile_money':
      return mtnMobileMoney.requestPayment(request)
    
    case 'airtel_money':
      return airtelMoney.requestPayment(request)
    
    case 'card':
      return {
        success: false,
        status: 'failed',
        message: 'Card payments coming soon. Please use Mobile Money.'
      }
    
    case 'cash':
      // Cash payments are recorded manually
      return {
        success: true,
        transactionId: `CASH-${Date.now()}`,
        status: 'completed',
        message: 'Cash payment recorded.',
        provider: 'Cash'
      }
    
    default:
      return {
        success: false,
        status: 'failed',
        message: 'Unknown payment method'
      }
  }
}

// USSD Payment Menu (for *xxx# integration)
export const ussdPaymentMenu = {
  mainMenu: `Welcome to LWSC Bill Payment
1. Pay Water Bill
2. Check Balance
3. Payment History
4. Report Leak
0. Exit`,

  paymentMenu: `Enter Account Number:`,
  
  confirmPayment: (account: string, amount: number) => 
    `Pay K${amount.toLocaleString()} for account ${account}?
1. Confirm
2. Cancel`,

  success: (ref: string) => `Payment successful!
Reference: ${ref}
Thank you for using LWSC.`,

  failure: (reason: string) => `Payment failed: ${reason}
Please try again or contact support.`
}
