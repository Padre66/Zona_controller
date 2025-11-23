using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.FileProviders;
using Microsoft.Extensions.Hosting;
using System.IO;

var builder = WebApplication.CreateBuilder(args);

// ---- PORT BEÁLLÍTÁS ----
builder.WebHost.UseUrls("http://0.0.0.0:8000");

// ---- SZOLGÁLTATÁSOK ----
builder.Services.AddSingleton<AuthService>();

var app = builder.Build();

// ---- STATIKUS FÁJLOK GYÖKERE: webserver mappa ----
var webRoot = Path.Combine(Directory.GetCurrentDirectory(), "webserver");
app.UseStaticFiles(new StaticFileOptions
{
    FileProvider = new PhysicalFileProvider(webRoot),
    RequestPath = ""
});

// ---- LOGIN API ----
app.MapPost("/api/login", async (HttpContext context, AuthService auth) =>
{
    var form = await context.Request.ReadFormAsync();
    var username = form["username"].ToString();
    var password = form["password"].ToString();

    var role = auth.ValidateUser(username, password);

    if (role == null)
    {
        context.Response.StatusCode = StatusCodes.Status401Unauthorized;
        await context.Response.WriteAsJsonAsync(new { success = false, message = "Hibás felhasználónév vagy jelszó" });
        return;
    }

    await context.Response.WriteAsJsonAsync(new { success = true, role });
});

// ---- ALAP (ROOT) -> LOGIN OLDALRA IRÁNYÍTÁS ----
app.MapGet("/", async context =>
{
    context.Response.Redirect("/login/login.html");
});

app.Run();
