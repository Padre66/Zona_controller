using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var builder = WebApplication.CreateBuilder(args);

builder.WebHost.UseUrls("http://0.0.0.0:8000");

// statikus fájlok kiszolgálása
builder.Services.AddDirectoryBrowser();

// egyszerű auth service
builder.Services.AddSingleton<AuthService>();

var app = builder.Build();

app.UseDefaultFiles();      // index.html keresése
app.UseStaticFiles();       // wwwroot helyett most a jelenlegi mappa lesz
app.UseRouting();

// LOGIN API
app.MapPost("/api/login", async (HttpContext context, AuthService authService) =>
{
    var form = await context.Request.ReadFormAsync();
    var username = form["username"].ToString();
    var password = form["password"].ToString();

    var role = authService.ValidateUser(username, password);

    if (role == null)
    {
        context.Response.StatusCode = StatusCodes.Status401Unauthorized;
        await context.Response.WriteAsJsonAsync(new { success = false, message = "Hibás felhasználónév vagy jelszó" });
        return;
    }

    await context.Response.WriteAsJsonAsync(new { success = true, role });
});

app.Run();
