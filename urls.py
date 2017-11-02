# coding=utf8
import os
from views import Index

URLMAPS = {
    "/": Index.as_view()
}