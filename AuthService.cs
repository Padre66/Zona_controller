using System;
using System.Collections.Generic;

public class AuthService
{
    private readonly Dictionary<string, (string Password, string Role)> _users =
        new(StringComparer.OrdinalIgnoreCase)
        {
            { "diag",      ("diag123",     "Diag") },
            { "admin",     ("admin123",    "Admin") },
            { "superuser", ("super123",    "Superuser") }
        };

    public string? ValidateUser(string username, string password)
    {
        if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(password))
            return null;

        if (_users.TryGetValue(username, out var user) && user.Password == password)
            return user.Role;

        return null;
    }
}
