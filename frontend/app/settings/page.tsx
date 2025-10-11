'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ProtectedRoute } from '@/components/protected-route';
import { useAuth } from '@/contexts/auth-context';
import { useTheme } from '@/hooks/use-theme';
import { useToast } from '@/hooks/use-toast';
import { updateProfile, changePassword, deleteAccount } from '@/lib/utils/auth';
import { User, LogOut, Trash2, Save, Moon, Sun } from 'lucide-react';

function SettingsContent() {
  const router = useRouter();
  const { toast } = useToast();
  const { user, logout, updateUser } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(user?.name || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const getUserInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const handleUpdateProfile = () => {
    if (!user) return;

    const result = updateProfile(user.id, { name });
    if (result.success) {
      updateUser({ name });
      setIsEditing(false);
      toast({
        title: 'Profile updated',
        description: 'Your profile has been updated successfully',
      });
    } else {
      toast({
        title: 'Update failed',
        description: result.error || 'Failed to update profile',
        variant: 'destructive',
      });
    }
  };

  const handleChangePassword = () => {
    if (!user) return;

    if (newPassword !== confirmPassword) {
      toast({
        title: 'Passwords do not match',
        description: 'Please make sure your passwords match',
        variant: 'destructive',
      });
      return;
    }

    const result = changePassword(user.id, currentPassword, newPassword);
    if (result.success) {
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setIsChangingPassword(false);
      toast({
        title: 'Password changed',
        description: 'Your password has been changed successfully',
      });
    } else {
      toast({
        title: 'Password change failed',
        description: result.error || 'Failed to change password',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteAccount = () => {
    if (!user) return;

    const confirmed = confirm(
      'Are you sure you want to delete your account? This action cannot be undone and will delete all your data including conversation history.'
    );

    if (confirmed) {
      const result = deleteAccount(user.id);
      if (result.success) {
        toast({
          title: 'Account deleted',
          description: 'Your account has been deleted successfully',
        });
        router.push('/login');
      } else {
        toast({
          title: 'Delete failed',
          description: result.error || 'Failed to delete account',
          variant: 'destructive',
        });
      }
    }
  };

  const handleLogout = () => {
    logout();
    toast({
      title: 'Logged out',
      description: 'You have been logged out successfully',
    });
    router.push('/login');
  };

  if (!user) return null;

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      <div className="space-y-6">
        {/* Profile Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Profile Information
            </CardTitle>
            <CardDescription>
              Manage your personal information and account details
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-4">
              <Avatar className="h-20 w-20">
                <AvatarFallback className="bg-primary text-primary-foreground text-2xl">
                  {getUserInitials(user.name)}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="text-sm text-muted-foreground">Profile Picture</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Using initials avatar
                </p>
              </div>
            </div>

            <Separator />

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <div className="flex gap-2">
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    disabled={!isEditing}
                  />
                  {isEditing ? (
                    <>
                      <Button onClick={handleUpdateProfile} size="sm">
                        <Save className="h-4 w-4 mr-2" />
                        Save
                      </Button>
                      <Button
                        onClick={() => {
                          setName(user.name);
                          setIsEditing(false);
                        }}
                        variant="outline"
                        size="sm"
                      >
                        Cancel
                      </Button>
                    </>
                  ) : (
                    <Button onClick={() => setIsEditing(true)} variant="outline" size="sm">
                      Edit
                    </Button>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" value={user.email} disabled />
                <p className="text-xs text-muted-foreground">
                  Email cannot be changed
                </p>
              </div>
            </div>

            <Separator />

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium">Change Password</h3>
                  <p className="text-xs text-muted-foreground">
                    Update your password to keep your account secure
                  </p>
                </div>
                <Button
                  onClick={() => setIsChangingPassword(!isChangingPassword)}
                  variant="outline"
                  size="sm"
                >
                  {isChangingPassword ? 'Cancel' : 'Change Password'}
                </Button>
              </div>

              {isChangingPassword && (
                <div className="space-y-3 pt-2">
                  <div className="space-y-2">
                    <Label htmlFor="currentPassword">Current Password</Label>
                    <Input
                      id="currentPassword"
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="Enter current password"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="newPassword">New Password</Label>
                    <Input
                      id="newPassword"
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Enter new password"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword">Confirm New Password</Label>
                    <Input
                      id="confirmPassword"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Confirm new password"
                    />
                  </div>
                  <Button onClick={handleChangePassword} className="w-full">
                    Update Password
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Appearance Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {theme === 'light' ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
              Appearance
            </CardTitle>
            <CardDescription>
              Customize how MedSearch AI looks on your device
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Theme</Label>
              <div className="flex gap-2">
                <Button
                  variant={theme === 'light' ? 'default' : 'outline'}
                  onClick={() => {
                    if (theme !== 'light') toggleTheme();
                  }}
                  size="sm"
                >
                  <Sun className="h-4 w-4 mr-2" />
                  Light
                </Button>
                <Button
                  variant={theme === 'dark' ? 'default' : 'outline'}
                  onClick={() => {
                    if (theme !== 'dark') toggleTheme();
                  }}
                  size="sm"
                >
                  <Moon className="h-4 w-4 mr-2" />
                  Dark
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Choose your preferred color scheme
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="border-red-200 dark:border-red-900">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
              <Trash2 className="h-5 w-5" />
              Danger Zone
            </CardTitle>
            <CardDescription>
              Irreversible and destructive actions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between p-4 border border-red-200 dark:border-red-900 rounded-lg">
                <div>
                  <h3 className="text-sm font-medium">Delete Account</h3>
                  <p className="text-xs text-muted-foreground">
                    Permanently delete your account and all associated data
                  </p>
                </div>
                <Button
                  onClick={handleDeleteAccount}
                  variant="destructive"
                  size="sm"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Account
                </Button>
              </div>

              <div className="flex items-center justify-between p-4 border border-red-200 dark:border-red-900 rounded-lg">
                <div>
                  <h3 className="text-sm font-medium">Clear All Conversations</h3>
                  <p className="text-xs text-muted-foreground">
                    Delete all your conversation history
                  </p>
                </div>
                <Button
                  onClick={() => {
                    const confirmed = confirm(
                      'Are you sure you want to delete all conversations? This action cannot be undone.'
                    );
                    if (confirmed) {
                      const keysToRemove: string[] = [];
                      for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        if (
                          key &&
                          (key.startsWith('medsearch_conversation_') ||
                            key === 'medsearch_conversations' ||
                            key === 'medsearch_search_history')
                        ) {
                          keysToRemove.push(key);
                        }
                      }
                      keysToRemove.forEach((key) => localStorage.removeItem(key));
                      toast({
                        title: 'Conversations cleared',
                        description: 'All your conversations have been deleted',
                      });
                    }
                  }}
                  variant="destructive"
                  size="sm"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear All
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Logout Button */}
        <Card>
          <CardContent className="pt-6">
            <Button
              onClick={handleLogout}
              variant="outline"
              className="w-full"
              size="lg"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Log Out
            </Button>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

export default function SettingsPage() {
  return (
    <ProtectedRoute>
      <SettingsContent />
    </ProtectedRoute>
  );
}

