import { NextRequest, NextResponse } from 'next/server'
import crypto from 'crypto'

// In-memory user storage (persists during serverless function lifecycle)
const users: Map<string, UserRecord> = new Map()

interface UserRecord {
  id: string
  username: string
  password_hash: string
  name: string
  email: string
  role: 'admin' | 'operator' | 'technician'
  department?: string
  phone?: string
  status: 'active' | 'inactive'
  created_at: string
  last_login?: string
}

// Hash password
function hashPassword(password: string): string {
  return crypto.createHash('sha256').update(password).digest('hex')
}

// Initialize default users
function initializeDefaultUsers() {
  if (users.size === 0) {
    const defaultUsers: Omit<UserRecord, 'password_hash'>[] = [
      {
        id: 'user-001',
        username: 'admin',
        name: 'System Administrator',
        email: 'admin@lwsc.local',
        role: 'admin',
        department: 'IT',
        status: 'active',
        created_at: '2026-01-01T00:00:00Z'
      },
      {
        id: 'user-002',
        username: 'operator',
        name: 'Control Room Operator',
        email: 'operator@lwsc.local',
        role: 'operator',
        department: 'Operations',
        status: 'active',
        created_at: '2026-01-01T00:00:00Z'
      },
      {
        id: 'user-003',
        username: 'technician',
        name: 'Field Technician',
        email: 'tech@lwsc.local',
        role: 'technician',
        department: 'Field Operations',
        status: 'active',
        created_at: '2026-01-01T00:00:00Z'
      },
      {
        id: 'user-004',
        username: 'denuel',
        name: 'Denuel',
        email: 'denuel@lwsc.local',
        role: 'admin',
        department: 'Management',
        status: 'active',
        created_at: '2026-01-01T00:00:00Z'
      }
    ]

    // Default passwords
    const passwords: Record<string, string> = {
      'admin': 'admin123',
      'operator': 'operator123',
      'technician': 'technician123',
      'denuel': 'denuel123'
    }

    defaultUsers.forEach(user => {
      const password = passwords[user.username] || 'password123'
      users.set(user.username.toLowerCase(), {
        ...user,
        password_hash: hashPassword(password)
      })
    })

    console.log('[Auth] Initialized default users:', Array.from(users.keys()))
  }
}

// Generate access token
function generateAccessToken(userId: string): string {
  const timestamp = Date.now()
  const random = crypto.randomBytes(16).toString('hex')
  return crypto.createHash('sha256').update(`${userId}-${timestamp}-${random}`).digest('hex')
}

// POST - Login user
export async function POST(request: NextRequest) {
  try {
    initializeDefaultUsers()
    
    const body = await request.json()
    const { username, password } = body
    
    if (!username || !password) {
      return NextResponse.json(
        { success: false, error: 'Username and password are required' },
        { status: 400 }
      )
    }
    
    const usernameKey = username.toLowerCase().trim()
    const user = users.get(usernameKey)
    
    if (!user) {
      console.log(`[Auth] Login failed - user not found: ${username}`)
      return NextResponse.json(
        { success: false, error: 'Invalid username or password' },
        { status: 401 }
      )
    }
    
    // Check if user is active
    if (user.status === 'inactive') {
      return NextResponse.json(
        { success: false, error: 'Account is disabled. Contact administrator.' },
        { status: 403 }
      )
    }
    
    // Verify password
    const passwordHash = hashPassword(password)
    if (user.password_hash !== passwordHash) {
      console.log(`[Auth] Login failed - wrong password for: ${username}`)
      console.log(`[Auth] Expected: ${user.password_hash.substring(0, 10)}...`)
      console.log(`[Auth] Got: ${passwordHash.substring(0, 10)}...`)
      return NextResponse.json(
        { success: false, error: 'Invalid username or password' },
        { status: 401 }
      )
    }
    
    // Update last login time
    user.last_login = new Date().toISOString()
    
    // Generate access token
    const accessToken = generateAccessToken(user.id)
    
    console.log(`[Auth] Login successful: ${username} (${user.role})`)
    
    return NextResponse.json({
      success: true,
      message: 'Login successful',
      user: {
        id: user.id,
        username: user.username,
        name: user.name,
        email: user.email,
        role: user.role,
        department: user.department,
        phone: user.phone
      },
      access_token: accessToken
    })
    
  } catch (error) {
    console.error('[Auth] Login error:', error)
    return NextResponse.json({
      success: false,
      error: 'Authentication failed',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}

// PUT - Register new user
export async function PUT(request: NextRequest) {
  try {
    initializeDefaultUsers()
    
    const body = await request.json()
    const { username, password, role, name, email, department, phone } = body
    
    // Validate required fields
    if (!username || !password || !role) {
      return NextResponse.json(
        { success: false, error: 'Username, password, and role are required' },
        { status: 400 }
      )
    }
    
    // Validate role
    if (!['admin', 'operator', 'technician'].includes(role)) {
      return NextResponse.json(
        { success: false, error: 'Invalid role. Must be admin, operator, or technician' },
        { status: 400 }
      )
    }
    
    const usernameKey = username.toLowerCase().trim()
    
    // Check if username already exists
    if (users.has(usernameKey)) {
      return NextResponse.json(
        { success: false, error: 'Username already exists' },
        { status: 409 }
      )
    }
    
    // Create new user
    const newUser: UserRecord = {
      id: `user-${Date.now()}`,
      username: usernameKey,
      password_hash: hashPassword(password),
      name: name || username,
      email: email || `${usernameKey}@lwsc.local`,
      role: role,
      department: department,
      phone: phone,
      status: 'active',
      created_at: new Date().toISOString()
    }
    
    users.set(usernameKey, newUser)
    
    console.log(`[Auth] User created: ${username} (${role})`)
    
    return NextResponse.json({
      success: true,
      message: 'User created successfully',
      user: {
        id: newUser.id,
        username: newUser.username,
        name: newUser.name,
        email: newUser.email,
        role: newUser.role
      }
    })
    
  } catch (error) {
    console.error('[Auth] Registration error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to create user'
    }, { status: 500 })
  }
}

// GET - List users
export async function GET() {
  try {
    initializeDefaultUsers()
    
    const userList = Array.from(users.values()).map(user => ({
      user_id: user.id,
      username: user.username,
      name: user.name,
      email: user.email,
      role: user.role,
      department: user.department,
      is_active: user.status === 'active',
      last_login: user.last_login,
      created_at: user.created_at
    }))
    
    return NextResponse.json({
      success: true,
      users: userList,
      total: userList.length
    })
    
  } catch (error) {
    console.error('[Auth] List users error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to fetch users'
    }, { status: 500 })
  }
}

// DELETE - Remove user
export async function DELETE(request: NextRequest) {
  try {
    initializeDefaultUsers()
    
    const { searchParams } = new URL(request.url)
    const username = searchParams.get('username')
    
    if (!username) {
      return NextResponse.json(
        { success: false, error: 'Username is required' },
        { status: 400 }
      )
    }
    
    const usernameKey = username.toLowerCase().trim()
    
    // Prevent deleting system admin
    if (usernameKey === 'admin') {
      return NextResponse.json(
        { success: false, error: 'Cannot delete system administrator' },
        { status: 403 }
      )
    }
    
    if (!users.has(usernameKey)) {
      return NextResponse.json(
        { success: false, error: 'User not found' },
        { status: 404 }
      )
    }
    
    users.delete(usernameKey)
    
    console.log(`[Auth] User deleted: ${username}`)
    
    return NextResponse.json({
      success: true,
      message: 'User deleted successfully'
    })
    
  } catch (error) {
    console.error('[Auth] Delete user error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to delete user'
    }, { status: 500 })
  }
}
