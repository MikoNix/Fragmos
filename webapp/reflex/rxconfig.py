import reflex as rx

config = rx.Config(
    app_name="koritsu",
    api_url="http://localhost:8002",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)