import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        // For demo purposes, accept any email/password combo
        // In production, validate against your database
        if (credentials?.email && credentials?.password) {
          // Generate a consistent user ID from email for multi-tenancy
          const email = credentials.email as string;
          const userId = Buffer.from(email).toString('base64').replace(/[^a-zA-Z0-9]/g, '').slice(0, 20);

          return {
            id: userId,
            email: email,
            name: email.split('@')[0],
          };
        }
        return null;
      },
    }),
  ],
  pages: {
    signIn: '/sign-in',
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user && token.id) {
        session.user.id = token.id as string;
      }
      return session;
    },
  },
  session: {
    strategy: 'jwt',
  },
});
