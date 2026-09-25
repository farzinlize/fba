<div align="center">

<img alt="The logo includes the abstract combination of the three letters FBA, forming a lightning bolt that seems to spread out from the ground" width="320" src="https://wu-clan.github.io/picx-images-hosting/logo/fba.png">

# FastAPI Best Architecture

Enterprise-level backend architecture solution

English | [Simplified Chinese](./README.zh-CN.md) | [فارسی](./README.fa-IR.md)

[![GitHub](https://img.shields.io/github/license/fastapi-practices/fastapi_best_architecture)](https://github.com/fastapi-practices/fastapi_best_architecture/blob/master/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-%2300758f)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.0%2B-%23336791)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-%23778877)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
![Docker](https://img.shields.io/badge/Docker-%232496ED?logo=docker&logoColor=white)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?logo=discord&logoColor=white)](https://discord.com/invite/yNN3wTbVAC)
![Discord](https://img.shields.io/discord/1185035164577972344)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/fastapi-practices/fastapi_best_architecture)

</div>

## Three-tier architecture

MVC is a common design pattern in Python web applications. This project uses a three-tier architecture
with an opinionated directory structure instead of a traditional multi-app layout, such as those used in
Django or Spring Boot. You can adapt the structure to suit your project.

| Workflow       | Java           | fastapi_best_architecture |
|----------------|----------------|---------------------------|
| View           | controller     | api                       |
| Data transfer  | dto            | schema                    |
| Business logic | service + impl | service                   |
| Data access    | dao / mapper   | crud                      |
| Model          | model / entity | model                     |

## Help

For more details, please check
the [official documentation](https://fastapi-practices.github.io/fastapi_best_architecture_docs/)

## Languages

The README is available in English, [Simplified Chinese](./README.zh-CN.md), and [Persian (Farsi)](./README.fa-IR.md).
For localized API response and validation messages, send `Accept-Language: en-US`, `zh-CN`, or `fa-IR`.
The short codes `en`, `zh`, and `fa` are also supported. Configure `I18N_DEFAULT_LANGUAGE` to choose the
language used when the header is absent; the existing default is `zh-CN`.
Developer documentation, API descriptions, and messages outside the locale system are in English.

## Sponsors

<div align="center">
  <table>
    <tr>
      <td align="center">
        <a href="https://claude.uy/home">
          <img src="https://purple-sun-4f5a.wuyao1243.workers.dev/" alt="Claude.uy" width="400">
        </a>
      </td>
    </tr>
  </table>
</div>

## Contributors

<a href="https://github.com/fastapi-practices/fastapi_best_architecture/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=fastapi-practices/fastapi_best_architecture"/>
</a>

## Special thanks

- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/latest/)
- [SQLAlchemy](https://docs.sqlalchemy.org/en/20/)
- [Casbin](https://casbin.org/zh/)
- [Ruff](https://beta.ruff.rs/docs/)
- ...

## Interactivity

[Discord](https://wu-clan.github.io/homepage/)

## License

This project is licensed by the terms of
the [MIT](https://github.com/fastapi-practices/fastapi_best_architecture/blob/master/LICENSE) license

[![Stargazers over time](https://starchart.cc/fastapi-practices/fastapi_best_architecture.svg?variant=adaptive)](https://starchart.cc/fastapi-practices/fastapi_best_architecture)
