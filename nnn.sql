PGDMP  .                    }            ganadero_anwt    16.9 (Debian 16.9-1.pgdg120+1)    17.5 ê    a           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false            b           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false            c           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false            d           1262    16389    ganadero_anwt    DATABASE     x   CREATE DATABASE ganadero_anwt WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.UTF8';
    DROP DATABASE ganadero_anwt;
                     ganadero_anwt_user    false            e           0    0    ganadero_anwt    DATABASE PROPERTIES     6   ALTER DATABASE ganadero_anwt SET "TimeZone" TO 'utc';
                          ganadero_anwt_user    false            Ú            1259    16415    alarmas_enviadas    TABLE     A  CREATE TABLE public.alarmas_enviadas (
    id integer NOT NULL,
    usuario_id integer,
    tipo character varying(50) NOT NULL,
    referencia_id integer NOT NULL,
    descripcion text,
    fecha_envio timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    email character varying(100) NOT NULL,
    mensaje text
);
 $   DROP TABLE public.alarmas_enviadas;
       public         heap r       ganadero_anwt_user    false            Ù            1259    16414    alarmas_enviadas_id_seq    SEQUENCE        CREATE SEQUENCE public.alarmas_enviadas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.alarmas_enviadas_id_seq;
       public               ganadero_anwt_user    false    218            f           0    0    alarmas_enviadas_id_seq    SEQUENCE OWNED BY     S   ALTER SEQUENCE public.alarmas_enviadas_id_seq OWNED BY public.alarmas_enviadas.id;
          public               ganadero_anwt_user    false    217            Ü            1259    16430    animales    TABLE     ´  CREATE TABLE public.animales (
    id integer NOT NULL,
    numero_arete character varying(50) NOT NULL,
    nombre character varying(100),
    sexo character varying(10) NOT NULL,
    raza character varying(100),
    condicion character varying(10) NOT NULL,
    fecha_nacimiento date,
    propietario character varying(200),
    foto_path character varying(500),
    padre_arete character varying(50),
    madre_arete character varying(50),
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT animales_condicion_check CHECK (((condicion)::text = ANY ((ARRAY['Toro'::character varying, 'Torete'::character varying, 'Vaca'::character varying, 'Vacona'::character varying, 'Ternero'::character varying, 'Ternera'::character varying])::text[]))),
    CONSTRAINT animales_sexo_check CHECK (((sexo)::text = ANY ((ARRAY['Macho'::character varying, 'Hembra'::character varying])::text[])))
);
    DROP TABLE public.animales;
       public         heap r       ganadero_anwt_user    false            g           0    0    TABLE animales    COMMENT     G   COMMENT ON TABLE public.animales IS 'Registro de animales del ganado';
          public               ganadero_anwt_user    false    220            Û            1259    16429    animales_id_seq    SEQUENCE        CREATE SEQUENCE public.animales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.animales_id_seq;
       public               ganadero_anwt_user    false    220            h           0    0    animales_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.animales_id_seq OWNED BY public.animales.id;
          public               ganadero_anwt_user    false    219            à            1259    16464    animales_pastizal    TABLE     :  CREATE TABLE public.animales_pastizal (
    id integer NOT NULL,
    animal_id integer NOT NULL,
    pastizal_id integer NOT NULL,
    fecha_asignacion date NOT NULL,
    fecha_retiro date,
    observaciones text,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
 %   DROP TABLE public.animales_pastizal;
       public         heap r       ganadero_anwt_user    false            ß            1259    16463    animales_pastizal_id_seq    SEQUENCE        CREATE SEQUENCE public.animales_pastizal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 /   DROP SEQUENCE public.animales_pastizal_id_seq;
       public               ganadero_anwt_user    false    224            i           0    0    animales_pastizal_id_seq    SEQUENCE OWNED BY     U   ALTER SEQUENCE public.animales_pastizal_id_seq OWNED BY public.animales_pastizal.id;
          public               ganadero_anwt_user    false    223            â            1259    16489 	   auditoria    TABLE       CREATE TABLE public.auditoria (
    id integer NOT NULL,
    usuario_id integer,
    accion character varying(50) NOT NULL,
    tabla character varying(50) NOT NULL,
    registro_id integer,
    detalles text,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.auditoria;
       public         heap r       ganadero_anwt_user    false            á            1259    16488    auditoria_id_seq    SEQUENCE        CREATE SEQUENCE public.auditoria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.auditoria_id_seq;
       public               ganadero_anwt_user    false    226            j           0    0    auditoria_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.auditoria_id_seq OWNED BY public.auditoria.id;
          public               ganadero_anwt_user    false    225            ä            1259    16504    carbunco    TABLE     C  CREATE TABLE public.carbunco (
    id integer NOT NULL,
    animal_id integer NOT NULL,
    fecha_aplicacion date NOT NULL,
    fecha_proxima date NOT NULL,
    dosis character varying(50),
    observaciones text,
    usuario_id integer NOT NULL,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.carbunco;
       public         heap r       ganadero_anwt_user    false            æ            1259    16524    carbunco_animal    TABLE        CREATE TABLE public.carbunco_animal (
    id integer NOT NULL,
    carbunco_id integer NOT NULL,
    animal_id integer NOT NULL
);
 #   DROP TABLE public.carbunco_animal;
       public         heap r       ganadero_anwt_user    false            å            1259    16523    carbunco_animal_id_seq    SEQUENCE        CREATE SEQUENCE public.carbunco_animal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.carbunco_animal_id_seq;
       public               ganadero_anwt_user    false    230            k           0    0    carbunco_animal_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.carbunco_animal_id_seq OWNED BY public.carbunco_animal.id;
          public               ganadero_anwt_user    false    229            ã            1259    16503    carbunco_id_seq    SEQUENCE        CREATE SEQUENCE public.carbunco_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.carbunco_id_seq;
       public               ganadero_anwt_user    false    228            l           0    0    carbunco_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.carbunco_id_seq OWNED BY public.carbunco.id;
          public               ganadero_anwt_user    false    227            è            1259    16541    categorias_gasto    TABLE     æ   CREATE TABLE public.categorias_gasto (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
 $   DROP TABLE public.categorias_gasto;
       public         heap r       ganadero_anwt_user    false            ç            1259    16540    categorias_gasto_id_seq    SEQUENCE        CREATE SEQUENCE public.categorias_gasto_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.categorias_gasto_id_seq;
       public               ganadero_anwt_user    false    232            m           0    0    categorias_gasto_id_seq    SEQUENCE OWNED BY     S   ALTER SEQUENCE public.categorias_gasto_id_seq OWNED BY public.categorias_gasto.id;
          public               ganadero_anwt_user    false    231            ê            1259    16556    categorias_ingreso    TABLE     è   CREATE TABLE public.categorias_ingreso (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
 &   DROP TABLE public.categorias_ingreso;
       public         heap r       ganadero_anwt_user    false            é            1259    16555    categorias_ingreso_id_seq    SEQUENCE        CREATE SEQUENCE public.categorias_ingreso_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 0   DROP SEQUENCE public.categorias_ingreso_id_seq;
       public               ganadero_anwt_user    false    234            n           0    0    categorias_ingreso_id_seq    SEQUENCE OWNED BY     W   ALTER SEQUENCE public.categorias_ingreso_id_seq OWNED BY public.categorias_ingreso.id;
          public               ganadero_anwt_user    false    233            ì            1259    16571    config_alarmas    TABLE     R  CREATE TABLE public.config_alarmas (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    tipo character varying(50) NOT NULL,
    dias_anticipacion integer DEFAULT 7 NOT NULL,
    activo boolean DEFAULT true,
    email character varying(100) NOT NULL,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
 "   DROP TABLE public.config_alarmas;
       public         heap r       ganadero_anwt_user    false            ë            1259    16570    config_alarmas_id_seq    SEQUENCE        CREATE SEQUENCE public.config_alarmas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 ,   DROP SEQUENCE public.config_alarmas_id_seq;
       public               ganadero_anwt_user    false    236            o           0    0    config_alarmas_id_seq    SEQUENCE OWNED BY     O   ALTER SEQUENCE public.config_alarmas_id_seq OWNED BY public.config_alarmas.id;
          public               ganadero_anwt_user    false    235            î            1259    16586    config_email    TABLE       CREATE TABLE public.config_email (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    smtp_server character varying(100) NOT NULL,
    smtp_port integer NOT NULL,
    smtp_user character varying(100) NOT NULL,
    smtp_password character varying(255) NOT NULL,
    from_email character varying(100) NOT NULL,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
     DROP TABLE public.config_email;
       public         heap r       ganadero_anwt_user    false            í            1259    16585    config_email_id_seq    SEQUENCE        CREATE SEQUENCE public.config_email_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.config_email_id_seq;
       public               ganadero_anwt_user    false    238            p           0    0    config_email_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.config_email_id_seq OWNED BY public.config_email.id;
          public               ganadero_anwt_user    false    237            ð            1259    16601    desparasitaciones    TABLE     h  CREATE TABLE public.desparasitaciones (
    id integer NOT NULL,
    animal_id integer NOT NULL,
    fecha_aplicacion date NOT NULL,
    producto character varying(100) NOT NULL,
    dosis character varying(50),
    fecha_proxima date,
    observaciones text,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
 %   DROP TABLE public.desparasitaciones;
       public         heap r       ganadero_anwt_user    false            ï            1259    16600    desparasitaciones_id_seq    SEQUENCE        CREATE SEQUENCE public.desparasitaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 /   DROP SEQUENCE public.desparasitaciones_id_seq;
       public               ganadero_anwt_user    false    240            q           0    0    desparasitaciones_id_seq    SEQUENCE OWNED BY     U   ALTER SEQUENCE public.desparasitaciones_id_seq OWNED BY public.desparasitaciones.id;
          public               ganadero_anwt_user    false    239            ò            1259    16621 	   empleados    TABLE       CREATE TABLE public.empleados (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    apellido character varying(100),
    cargo character varying(100),
    telefono character varying(20),
    email character varying(100),
    direccion character varying(255),
    fecha_ingreso date,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.empleados;
       public         heap r       ganadero_anwt_user    false            ñ            1259    16620    empleados_id_seq    SEQUENCE        CREATE SEQUENCE public.empleados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.empleados_id_seq;
       public               ganadero_anwt_user    false    242            r           0    0    empleados_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.empleados_id_seq OWNED BY public.empleados.id;
          public               ganadero_anwt_user    false    241            ô            1259    16636    equipos    TABLE       CREATE TABLE public.equipos (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    estado character varying(20) DEFAULT 'Activo'::character varying,
    ubicacion character varying(100),
    fecha_adquisicion date,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT equipos_estado_check CHECK (((estado)::text = ANY ((ARRAY['Activo'::character varying, 'En mantenimiento'::character varying, 'Inactivo'::character varying])::text[])))
);
    DROP TABLE public.equipos;
       public         heap r       ganadero_anwt_user    false            ó            1259    16635    equipos_id_seq    SEQUENCE        CREATE SEQUENCE public.equipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 %   DROP SEQUENCE public.equipos_id_seq;
       public               ganadero_anwt_user    false    244            s           0    0    equipos_id_seq    SEQUENCE OWNED BY     A   ALTER SEQUENCE public.equipos_id_seq OWNED BY public.equipos.id;
          public               ganadero_anwt_user    false    243            ö            1259    16653    fiebre_aftosa    TABLE     H  CREATE TABLE public.fiebre_aftosa (
    id integer NOT NULL,
    animal_id integer NOT NULL,
    fecha_aplicacion date NOT NULL,
    fecha_proxima date NOT NULL,
    dosis character varying(50),
    observaciones text,
    usuario_id integer NOT NULL,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
 !   DROP TABLE public.fiebre_aftosa;
       public         heap r       ganadero_anwt_user    false            õ            1259    16652    fiebre_aftosa_id_seq    SEQUENCE        CREATE SEQUENCE public.fiebre_aftosa_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.fiebre_aftosa_id_seq;
       public               ganadero_anwt_user    false    246            t           0    0    fiebre_aftosa_id_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.fiebre_aftosa_id_seq OWNED BY public.fiebre_aftosa.id;
          public               ganadero_anwt_user    false    245            ø            1259    16673    gastos    TABLE     6  CREATE TABLE public.gastos (
    id integer NOT NULL,
    fecha date NOT NULL,
    categoria_id integer NOT NULL,
    monto numeric(10,2) NOT NULL,
    descripcion text,
    comprobante character varying(255),
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.gastos;
       public         heap r       ganadero_anwt_user    false            u           0    0    TABLE gastos    COMMENT     D   COMMENT ON TABLE public.gastos IS 'Registro de gastos de la finca';
          public               ganadero_anwt_user    false    248            ÷            1259    16672    gastos_id_seq    SEQUENCE        CREATE SEQUENCE public.gastos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 $   DROP SEQUENCE public.gastos_id_seq;
       public               ganadero_anwt_user    false    248            v           0    0    gastos_id_seq    SEQUENCE OWNED BY     ?   ALTER SEQUENCE public.gastos_id_seq OWNED BY public.gastos.id;
          public               ganadero_anwt_user    false    247            ú            1259    16693 
   genealogia    TABLE     ä  CREATE TABLE public.genealogia (
    id integer NOT NULL,
    animal_id integer NOT NULL,
    padre_arete character varying(50),
    madre_arete character varying(50),
    abuelo_paterno_arete character varying(50),
    abuela_paterna_arete character varying(50),
    abuelo_materno_arete character varying(50),
    abuela_materna_arete character varying(50),
    observaciones text,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.genealogia;
       public         heap r       ganadero_anwt_user    false            ù            1259    16692    genealogia_id_seq    SEQUENCE        CREATE SEQUENCE public.genealogia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 (   DROP SEQUENCE public.genealogia_id_seq;
       public               ganadero_anwt_user    false    250            w           0    0    genealogia_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.genealogia_id_seq OWNED BY public.genealogia.id;
          public               ganadero_anwt_user    false    249            ü            1259    16713    gestaciones    TABLE     2  CREATE TABLE public.gestaciones (
    id integer NOT NULL,
    animal_id integer NOT NULL,
    fecha_monta date NOT NULL,
    fecha_probable_parto date NOT NULL,
    estado character varying(15) DEFAULT 'En GestaciÃ³n'::character varying NOT NULL,
    observaciones text,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT gestaciones_estado_check CHECK (((estado)::text = ANY ((ARRAY['En GestaciÃ³n'::character varying, 'Finalizado'::character varying, 'Abortado'::character varying])::text[])))
);
    DROP TABLE public.gestaciones;
       public         heap r       ganadero_anwt_user    false            x           0    0    TABLE gestaciones    COMMENT     L   COMMENT ON TABLE public.gestaciones IS 'Control de gestaciones del ganado';
          public               ganadero_anwt_user    false    252            û            1259    16712    gestaciones_id_seq    SEQUENCE        CREATE SEQUENCE public.gestaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 )   DROP SEQUENCE public.gestaciones_id_seq;
       public               ganadero_anwt_user    false    252            y           0    0    gestaciones_id_seq    SEQUENCE OWNED BY     I   ALTER SEQUENCE public.gestaciones_id_seq OWNED BY public.gestaciones.id;
          public               ganadero_anwt_user    false    251            þ            1259    16735    historial_contrasenas    TABLE     ã   CREATE TABLE public.historial_contrasenas (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    password_hash character varying(255) NOT NULL,
    fecha_cambio timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
 )   DROP TABLE public.historial_contrasenas;
       public         heap r       ganadero_anwt_user    false            ý            1259    16734    historial_contrasenas_id_seq    SEQUENCE        CREATE SEQUENCE public.historial_contrasenas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 3   DROP SEQUENCE public.historial_contrasenas_id_seq;
       public               ganadero_anwt_user    false    254            z           0    0    historial_contrasenas_id_seq    SEQUENCE OWNED BY     ]   ALTER SEQUENCE public.historial_contrasenas_id_seq OWNED BY public.historial_contrasenas.id;
          public               ganadero_anwt_user    false    253                        1259    16748    ingresos    TABLE     8  CREATE TABLE public.ingresos (
    id integer NOT NULL,
    fecha date NOT NULL,
    categoria_id integer NOT NULL,
    monto numeric(10,2) NOT NULL,
    descripcion text,
    comprobante character varying(255),
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.ingresos;
       public         heap r       ganadero_anwt_user    false            {           0    0    TABLE ingresos    COMMENT     H   COMMENT ON TABLE public.ingresos IS 'Registro de ingresos de la finca';
          public               ganadero_anwt_user    false    256            ÿ            1259    16747    ingresos_id_seq    SEQUENCE        CREATE SEQUENCE public.ingresos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.ingresos_id_seq;
       public               ganadero_anwt_user    false    256            |           0    0    ingresos_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.ingresos_id_seq OWNED BY public.ingresos.id;
          public               ganadero_anwt_user    false    255                       1259    16768    inseminaciones    TABLE     H  CREATE TABLE public.inseminaciones (
    id integer NOT NULL,
    animal_id integer NOT NULL,
    fecha_inseminacion date NOT NULL,
    tipo_inseminacion character varying(50) NOT NULL,
    semental character varying(100) NOT NULL,
    raza_semental character varying(100),
    codigo_pajuela character varying(100),
    inseminador character varying(100),
    observaciones text,
    estado character varying(50) DEFAULT 'Pendiente'::character varying,
    exitosa boolean,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    usuario_id integer NOT NULL
);
 "   DROP TABLE public.inseminaciones;
       public         heap r       ganadero_anwt_user    false                       1259    16767    inseminaciones_id_seq    SEQUENCE        CREATE SEQUENCE public.inseminaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 ,   DROP SEQUENCE public.inseminaciones_id_seq;
       public               ganadero_anwt_user    false    258            }           0    0    inseminaciones_id_seq    SEQUENCE OWNED BY     O   ALTER SEQUENCE public.inseminaciones_id_seq OWNED BY public.inseminaciones.id;
          public               ganadero_anwt_user    false    257            Þ            1259    16449 
   pastizales    TABLE     2  CREATE TABLE public.pastizales (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    ubicacion character varying(255),
    capacidad integer,
    estado character varying(15) DEFAULT 'Disponible'::character varying,
    tipo_hierba character varying(100),
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    usuario_id integer,
    CONSTRAINT pastizales_estado_check CHECK (((estado)::text = ANY ((ARRAY['Disponible'::character varying, 'En uso'::character varying, 'En descanso'::character varying])::text[])))
);
    DROP TABLE public.pastizales;
       public         heap r       ganadero_anwt_user    false            ~           0    0    TABLE pastizales    COMMENT     L   COMMENT ON TABLE public.pastizales IS 'Registro de pastizales disponibles';
          public               ganadero_anwt_user    false    222                       1259    16789    pastizales_animales    TABLE     ¶   CREATE TABLE public.pastizales_animales (
    id integer NOT NULL,
    pastizal_id integer NOT NULL,
    animal_id integer NOT NULL,
    fecha_ingreso date,
    fecha_salida date
);
 '   DROP TABLE public.pastizales_animales;
       public         heap r       ganadero_anwt_user    false                       1259    16788    pastizales_animales_id_seq    SEQUENCE        CREATE SEQUENCE public.pastizales_animales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 1   DROP SEQUENCE public.pastizales_animales_id_seq;
       public               ganadero_anwt_user    false    260                       0    0    pastizales_animales_id_seq    SEQUENCE OWNED BY     Y   ALTER SEQUENCE public.pastizales_animales_id_seq OWNED BY public.pastizales_animales.id;
          public               ganadero_anwt_user    false    259            Ý            1259    16448    pastizales_id_seq    SEQUENCE        CREATE SEQUENCE public.pastizales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 (   DROP SEQUENCE public.pastizales_id_seq;
       public               ganadero_anwt_user    false    222                       0    0    pastizales_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.pastizales_id_seq OWNED BY public.pastizales.id;
          public               ganadero_anwt_user    false    221                       1259    16806    registro_leche    TABLE     U  CREATE TABLE public.registro_leche (
    id integer NOT NULL,
    animal_id integer NOT NULL,
    fecha date NOT NULL,
    cantidad_manana numeric(10,2),
    cantidad_tarde numeric(10,2),
    total_dia numeric(10,2),
    observaciones text,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
 "   DROP TABLE public.registro_leche;
       public         heap r       ganadero_anwt_user    false                       0    0    TABLE registro_leche    COMMENT     U   COMMENT ON TABLE public.registro_leche IS 'Registro diario de producciÃ³n de leche';
          public               ganadero_anwt_user    false    262                       1259    16805    registro_leche_id_seq    SEQUENCE        CREATE SEQUENCE public.registro_leche_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 ,   DROP SEQUENCE public.registro_leche_id_seq;
       public               ganadero_anwt_user    false    262                       0    0    registro_leche_id_seq    SEQUENCE OWNED BY     O   ALTER SEQUENCE public.registro_leche_id_seq OWNED BY public.registro_leche.id;
          public               ganadero_anwt_user    false    261            
           1259    16841    registro_vacunas    TABLE     8  CREATE TABLE public.registro_vacunas (
    id integer NOT NULL,
    animal_id integer NOT NULL,
    vacuna_id integer NOT NULL,
    fecha_aplicacion date NOT NULL,
    fecha_proxima date,
    observaciones text,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
 $   DROP TABLE public.registro_vacunas;
       public         heap r       ganadero_anwt_user    false            	           1259    16840    registro_vacunas_id_seq    SEQUENCE        CREATE SEQUENCE public.registro_vacunas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.registro_vacunas_id_seq;
       public               ganadero_anwt_user    false    266                       0    0    registro_vacunas_id_seq    SEQUENCE OWNED BY     S   ALTER SEQUENCE public.registro_vacunas_id_seq OWNED BY public.registro_vacunas.id;
          public               ganadero_anwt_user    false    265                       1259    16866    reproduccion    TABLE       CREATE TABLE public.reproduccion (
    id integer NOT NULL,
    animal_id integer NOT NULL,
    fecha_inseminacion date NOT NULL,
    fecha_parto_estimada date,
    estado character varying(10) DEFAULT 'Pendiente'::character varying,
    observaciones text,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT reproduccion_estado_check CHECK (((estado)::text = ANY ((ARRAY['Pendiente'::character varying, 'Exitoso'::character varying, 'Fallido'::character varying])::text[])))
);
     DROP TABLE public.reproduccion;
       public         heap r       ganadero_anwt_user    false                       1259    16865    reproduccion_id_seq    SEQUENCE        CREATE SEQUENCE public.reproduccion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.reproduccion_id_seq;
       public               ganadero_anwt_user    false    268                       0    0    reproduccion_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.reproduccion_id_seq OWNED BY public.reproduccion.id;
          public               ganadero_anwt_user    false    267                       1259    16888    tareas    TABLE       CREATE TABLE public.tareas (
    id integer NOT NULL,
    descripcion character varying(255) NOT NULL,
    estado character varying(15) DEFAULT 'Pendiente'::character varying,
    fecha_inicio date,
    fecha_fin date,
    empleado_id integer,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tareas_estado_check CHECK (((estado)::text = ANY ((ARRAY['Pendiente'::character varying, 'En Progreso'::character varying, 'Completada'::character varying])::text[])))
);
    DROP TABLE public.tareas;
       public         heap r       ganadero_anwt_user    false                       1259    16887    tareas_id_seq    SEQUENCE        CREATE SEQUENCE public.tareas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 $   DROP SEQUENCE public.tareas_id_seq;
       public               ganadero_anwt_user    false    270                       0    0    tareas_id_seq    SEQUENCE OWNED BY     ?   ALTER SEQUENCE public.tareas_id_seq OWNED BY public.tareas.id;
          public               ganadero_anwt_user    false    269            Ø            1259    16400    usuarios    TABLE     Ô  CREATE TABLE public.usuarios (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password character varying(255) NOT NULL,
    nombre character varying(100),
    apellido character varying(100),
    telefono character varying(20),
    direccion text,
    foto_perfil character varying(500),
    cargo character varying(100),
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.usuarios;
       public         heap r       ganadero_anwt_user    false                       0    0    TABLE usuarios    COMMENT     N   COMMENT ON TABLE public.usuarios IS 'Tabla de usuarios del sistema ganadero';
          public               ganadero_anwt_user    false    216            ×            1259    16399    usuarios_id_seq    SEQUENCE        CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.usuarios_id_seq;
       public               ganadero_anwt_user    false    216                       0    0    usuarios_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;
          public               ganadero_anwt_user    false    215                       1259    16908    vacuna    TABLE       CREATE TABLE public.vacuna (
    id integer NOT NULL,
    animal_id integer NOT NULL,
    usuario_id integer NOT NULL,
    tipo character varying(100) NOT NULL,
    fecha_aplicacion date,
    fecha_proxima date NOT NULL,
    dosis character varying(50),
    aplicada_por character varying(100),
    observaciones text,
    estado character varying(20) DEFAULT 'Activo'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.vacuna;
       public         heap r       ganadero_anwt_user    false                       1259    16907    vacuna_id_seq    SEQUENCE        CREATE SEQUENCE public.vacuna_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 $   DROP SEQUENCE public.vacuna_id_seq;
       public               ganadero_anwt_user    false    272                       0    0    vacuna_id_seq    SEQUENCE OWNED BY     ?   ALTER SEQUENCE public.vacuna_id_seq OWNED BY public.vacuna.id;
          public               ganadero_anwt_user    false    271                       1259    16826    vacunas    TABLE     ý   CREATE TABLE public.vacunas (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    periodo_aplicacion integer,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.vacunas;
       public         heap r       ganadero_anwt_user    false                       1259    16825    vacunas_id_seq    SEQUENCE        CREATE SEQUENCE public.vacunas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 %   DROP SEQUENCE public.vacunas_id_seq;
       public               ganadero_anwt_user    false    264                       0    0    vacunas_id_seq    SEQUENCE OWNED BY     A   ALTER SEQUENCE public.vacunas_id_seq OWNED BY public.vacunas.id;
          public               ganadero_anwt_user    false    263                       1259    16936    ventas_leche    TABLE     n  CREATE TABLE public.ventas_leche (
    id integer NOT NULL,
    fecha date NOT NULL,
    cantidad_litros numeric(10,2) NOT NULL,
    precio_litro numeric(10,2) NOT NULL,
    total numeric(10,2) NOT NULL,
    comprador character varying(200),
    observaciones text,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
     DROP TABLE public.ventas_leche;
       public         heap r       ganadero_anwt_user    false                       1259    16935    ventas_leche_id_seq    SEQUENCE        CREATE SEQUENCE public.ventas_leche_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.ventas_leche_id_seq;
       public               ganadero_anwt_user    false    274                       0    0    ventas_leche_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.ventas_leche_id_seq OWNED BY public.ventas_leche.id;
          public               ganadero_anwt_user    false    273                       1259    16951    vitaminizaciones    TABLE     g  CREATE TABLE public.vitaminizaciones (
    id integer NOT NULL,
    animal_id integer NOT NULL,
    fecha_aplicacion date NOT NULL,
    producto character varying(100) NOT NULL,
    dosis character varying(50),
    fecha_proxima date,
    observaciones text,
    usuario_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
 $   DROP TABLE public.vitaminizaciones;
       public         heap r       ganadero_anwt_user    false                       1259    16950    vitaminizaciones_id_seq    SEQUENCE        CREATE SEQUENCE public.vitaminizaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.vitaminizaciones_id_seq;
       public               ganadero_anwt_user    false    276                       0    0    vitaminizaciones_id_seq    SEQUENCE OWNED BY     S   ALTER SEQUENCE public.vitaminizaciones_id_seq OWNED BY public.vitaminizaciones.id;
          public               ganadero_anwt_user    false    275                       2604    16418    alarmas_enviadas id    DEFAULT     z   ALTER TABLE ONLY public.alarmas_enviadas ALTER COLUMN id SET DEFAULT nextval('public.alarmas_enviadas_id_seq'::regclass);
 B   ALTER TABLE public.alarmas_enviadas ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    218    217    218                       2604    16433    animales id    DEFAULT     j   ALTER TABLE ONLY public.animales ALTER COLUMN id SET DEFAULT nextval('public.animales_id_seq'::regclass);
 :   ALTER TABLE public.animales ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    219    220    220                       2604    16467    animales_pastizal id    DEFAULT     |   ALTER TABLE ONLY public.animales_pastizal ALTER COLUMN id SET DEFAULT nextval('public.animales_pastizal_id_seq'::regclass);
 C   ALTER TABLE public.animales_pastizal ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    223    224    224            
           2604    16492    auditoria id    DEFAULT     l   ALTER TABLE ONLY public.auditoria ALTER COLUMN id SET DEFAULT nextval('public.auditoria_id_seq'::regclass);
 ;   ALTER TABLE public.auditoria ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    225    226    226                       2604    16507    carbunco id    DEFAULT     j   ALTER TABLE ONLY public.carbunco ALTER COLUMN id SET DEFAULT nextval('public.carbunco_id_seq'::regclass);
 :   ALTER TABLE public.carbunco ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    228    227    228                       2604    16527    carbunco_animal id    DEFAULT     x   ALTER TABLE ONLY public.carbunco_animal ALTER COLUMN id SET DEFAULT nextval('public.carbunco_animal_id_seq'::regclass);
 A   ALTER TABLE public.carbunco_animal ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    229    230    230                       2604    16544    categorias_gasto id    DEFAULT     z   ALTER TABLE ONLY public.categorias_gasto ALTER COLUMN id SET DEFAULT nextval('public.categorias_gasto_id_seq'::regclass);
 B   ALTER TABLE public.categorias_gasto ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    231    232    232                       2604    16559    categorias_ingreso id    DEFAULT     ~   ALTER TABLE ONLY public.categorias_ingreso ALTER COLUMN id SET DEFAULT nextval('public.categorias_ingreso_id_seq'::regclass);
 D   ALTER TABLE public.categorias_ingreso ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    234    233    234                       2604    16574    config_alarmas id    DEFAULT     v   ALTER TABLE ONLY public.config_alarmas ALTER COLUMN id SET DEFAULT nextval('public.config_alarmas_id_seq'::regclass);
 @   ALTER TABLE public.config_alarmas ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    236    235    236                       2604    16589    config_email id    DEFAULT     r   ALTER TABLE ONLY public.config_email ALTER COLUMN id SET DEFAULT nextval('public.config_email_id_seq'::regclass);
 >   ALTER TABLE public.config_email ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    237    238    238                       2604    16604    desparasitaciones id    DEFAULT     |   ALTER TABLE ONLY public.desparasitaciones ALTER COLUMN id SET DEFAULT nextval('public.desparasitaciones_id_seq'::regclass);
 C   ALTER TABLE public.desparasitaciones ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    239    240    240                       2604    16624    empleados id    DEFAULT     l   ALTER TABLE ONLY public.empleados ALTER COLUMN id SET DEFAULT nextval('public.empleados_id_seq'::regclass);
 ;   ALTER TABLE public.empleados ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    242    241    242                       2604    16639 
   equipos id    DEFAULT     h   ALTER TABLE ONLY public.equipos ALTER COLUMN id SET DEFAULT nextval('public.equipos_id_seq'::regclass);
 9   ALTER TABLE public.equipos ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    244    243    244                        2604    16656    fiebre_aftosa id    DEFAULT     t   ALTER TABLE ONLY public.fiebre_aftosa ALTER COLUMN id SET DEFAULT nextval('public.fiebre_aftosa_id_seq'::regclass);
 ?   ALTER TABLE public.fiebre_aftosa ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    245    246    246            "           2604    16676 	   gastos id    DEFAULT     f   ALTER TABLE ONLY public.gastos ALTER COLUMN id SET DEFAULT nextval('public.gastos_id_seq'::regclass);
 8   ALTER TABLE public.gastos ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    248    247    248            $           2604    16696    genealogia id    DEFAULT     n   ALTER TABLE ONLY public.genealogia ALTER COLUMN id SET DEFAULT nextval('public.genealogia_id_seq'::regclass);
 <   ALTER TABLE public.genealogia ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    249    250    250            &           2604    16716    gestaciones id    DEFAULT     p   ALTER TABLE ONLY public.gestaciones ALTER COLUMN id SET DEFAULT nextval('public.gestaciones_id_seq'::regclass);
 =   ALTER TABLE public.gestaciones ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    251    252    252            )           2604    16738    historial_contrasenas id    DEFAULT        ALTER TABLE ONLY public.historial_contrasenas ALTER COLUMN id SET DEFAULT nextval('public.historial_contrasenas_id_seq'::regclass);
 G   ALTER TABLE public.historial_contrasenas ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    253    254    254            +           2604    16751    ingresos id    DEFAULT     j   ALTER TABLE ONLY public.ingresos ALTER COLUMN id SET DEFAULT nextval('public.ingresos_id_seq'::regclass);
 :   ALTER TABLE public.ingresos ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    256    255    256            -           2604    16771    inseminaciones id    DEFAULT     v   ALTER TABLE ONLY public.inseminaciones ALTER COLUMN id SET DEFAULT nextval('public.inseminaciones_id_seq'::regclass);
 @   ALTER TABLE public.inseminaciones ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    258    257    258                       2604    16452    pastizales id    DEFAULT     n   ALTER TABLE ONLY public.pastizales ALTER COLUMN id SET DEFAULT nextval('public.pastizales_id_seq'::regclass);
 <   ALTER TABLE public.pastizales ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    222    221    222            0           2604    16792    pastizales_animales id    DEFAULT        ALTER TABLE ONLY public.pastizales_animales ALTER COLUMN id SET DEFAULT nextval('public.pastizales_animales_id_seq'::regclass);
 E   ALTER TABLE public.pastizales_animales ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    260    259    260            1           2604    16809    registro_leche id    DEFAULT     v   ALTER TABLE ONLY public.registro_leche ALTER COLUMN id SET DEFAULT nextval('public.registro_leche_id_seq'::regclass);
 @   ALTER TABLE public.registro_leche ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    261    262    262            5           2604    16844    registro_vacunas id    DEFAULT     z   ALTER TABLE ONLY public.registro_vacunas ALTER COLUMN id SET DEFAULT nextval('public.registro_vacunas_id_seq'::regclass);
 B   ALTER TABLE public.registro_vacunas ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    265    266    266            7           2604    16869    reproduccion id    DEFAULT     r   ALTER TABLE ONLY public.reproduccion ALTER COLUMN id SET DEFAULT nextval('public.reproduccion_id_seq'::regclass);
 >   ALTER TABLE public.reproduccion ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    267    268    268            :           2604    16891 	   tareas id    DEFAULT     f   ALTER TABLE ONLY public.tareas ALTER COLUMN id SET DEFAULT nextval('public.tareas_id_seq'::regclass);
 8   ALTER TABLE public.tareas ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    269    270    270            ÿ           2604    16403    usuarios id    DEFAULT     j   ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);
 :   ALTER TABLE public.usuarios ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    216    215    216            =           2604    16911 	   vacuna id    DEFAULT     f   ALTER TABLE ONLY public.vacuna ALTER COLUMN id SET DEFAULT nextval('public.vacuna_id_seq'::regclass);
 8   ALTER TABLE public.vacuna ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    272    271    272            3           2604    16829 
   vacunas id    DEFAULT     h   ALTER TABLE ONLY public.vacunas ALTER COLUMN id SET DEFAULT nextval('public.vacunas_id_seq'::regclass);
 9   ALTER TABLE public.vacunas ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    264    263    264            A           2604    16939    ventas_leche id    DEFAULT     r   ALTER TABLE ONLY public.ventas_leche ALTER COLUMN id SET DEFAULT nextval('public.ventas_leche_id_seq'::regclass);
 >   ALTER TABLE public.ventas_leche ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    274    273    274            C           2604    16954    vitaminizaciones id    DEFAULT     z   ALTER TABLE ONLY public.vitaminizaciones ALTER COLUMN id SET DEFAULT nextval('public.vitaminizaciones_id_seq'::regclass);
 B   ALTER TABLE public.vitaminizaciones ALTER COLUMN id DROP DEFAULT;
       public               ganadero_anwt_user    false    276    275    276            T           2606    16423 &   alarmas_enviadas alarmas_enviadas_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.alarmas_enviadas
    ADD CONSTRAINT alarmas_enviadas_pkey PRIMARY KEY (id);
 P   ALTER TABLE ONLY public.alarmas_enviadas DROP CONSTRAINT alarmas_enviadas_pkey;
       public                 ganadero_anwt_user    false    218            V           2606    16442 "   animales animales_numero_arete_key 
   CONSTRAINT     e   ALTER TABLE ONLY public.animales
    ADD CONSTRAINT animales_numero_arete_key UNIQUE (numero_arete);
 L   ALTER TABLE ONLY public.animales DROP CONSTRAINT animales_numero_arete_key;
       public                 ganadero_anwt_user    false    220            `           2606    16472 (   animales_pastizal animales_pastizal_pkey 
   CONSTRAINT     f   ALTER TABLE ONLY public.animales_pastizal
    ADD CONSTRAINT animales_pastizal_pkey PRIMARY KEY (id);
 R   ALTER TABLE ONLY public.animales_pastizal DROP CONSTRAINT animales_pastizal_pkey;
       public                 ganadero_anwt_user    false    224            X           2606    16440    animales animales_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.animales
    ADD CONSTRAINT animales_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.animales DROP CONSTRAINT animales_pkey;
       public                 ganadero_anwt_user    false    220            b           2606    16497    auditoria auditoria_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT auditoria_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.auditoria DROP CONSTRAINT auditoria_pkey;
       public                 ganadero_anwt_user    false    226            f           2606    16529 $   carbunco_animal carbunco_animal_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.carbunco_animal
    ADD CONSTRAINT carbunco_animal_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.carbunco_animal DROP CONSTRAINT carbunco_animal_pkey;
       public                 ganadero_anwt_user    false    230            d           2606    16512    carbunco carbunco_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.carbunco
    ADD CONSTRAINT carbunco_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.carbunco DROP CONSTRAINT carbunco_pkey;
       public                 ganadero_anwt_user    false    228            h           2606    16549 &   categorias_gasto categorias_gasto_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.categorias_gasto
    ADD CONSTRAINT categorias_gasto_pkey PRIMARY KEY (id);
 P   ALTER TABLE ONLY public.categorias_gasto DROP CONSTRAINT categorias_gasto_pkey;
       public                 ganadero_anwt_user    false    232            j           2606    16564 *   categorias_ingreso categorias_ingreso_pkey 
   CONSTRAINT     h   ALTER TABLE ONLY public.categorias_ingreso
    ADD CONSTRAINT categorias_ingreso_pkey PRIMARY KEY (id);
 T   ALTER TABLE ONLY public.categorias_ingreso DROP CONSTRAINT categorias_ingreso_pkey;
       public                 ganadero_anwt_user    false    234            l           2606    16579 "   config_alarmas config_alarmas_pkey 
   CONSTRAINT     `   ALTER TABLE ONLY public.config_alarmas
    ADD CONSTRAINT config_alarmas_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.config_alarmas DROP CONSTRAINT config_alarmas_pkey;
       public                 ganadero_anwt_user    false    236            n           2606    16594    config_email config_email_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.config_email
    ADD CONSTRAINT config_email_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.config_email DROP CONSTRAINT config_email_pkey;
       public                 ganadero_anwt_user    false    238            p           2606    16609 (   desparasitaciones desparasitaciones_pkey 
   CONSTRAINT     f   ALTER TABLE ONLY public.desparasitaciones
    ADD CONSTRAINT desparasitaciones_pkey PRIMARY KEY (id);
 R   ALTER TABLE ONLY public.desparasitaciones DROP CONSTRAINT desparasitaciones_pkey;
       public                 ganadero_anwt_user    false    240            r           2606    16629    empleados empleados_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.empleados
    ADD CONSTRAINT empleados_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.empleados DROP CONSTRAINT empleados_pkey;
       public                 ganadero_anwt_user    false    242            t           2606    16646    equipos equipos_pkey 
   CONSTRAINT     R   ALTER TABLE ONLY public.equipos
    ADD CONSTRAINT equipos_pkey PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.equipos DROP CONSTRAINT equipos_pkey;
       public                 ganadero_anwt_user    false    244            v           2606    16661     fiebre_aftosa fiebre_aftosa_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.fiebre_aftosa
    ADD CONSTRAINT fiebre_aftosa_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.fiebre_aftosa DROP CONSTRAINT fiebre_aftosa_pkey;
       public                 ganadero_anwt_user    false    246            x           2606    16681    gastos gastos_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.gastos
    ADD CONSTRAINT gastos_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.gastos DROP CONSTRAINT gastos_pkey;
       public                 ganadero_anwt_user    false    248            {           2606    16701    genealogia genealogia_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.genealogia
    ADD CONSTRAINT genealogia_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.genealogia DROP CONSTRAINT genealogia_pkey;
       public                 ganadero_anwt_user    false    250            }           2606    16723    gestaciones gestaciones_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.gestaciones
    ADD CONSTRAINT gestaciones_pkey PRIMARY KEY (id);
 F   ALTER TABLE ONLY public.gestaciones DROP CONSTRAINT gestaciones_pkey;
       public                 ganadero_anwt_user    false    252                       2606    16741 0   historial_contrasenas historial_contrasenas_pkey 
   CONSTRAINT     n   ALTER TABLE ONLY public.historial_contrasenas
    ADD CONSTRAINT historial_contrasenas_pkey PRIMARY KEY (id);
 Z   ALTER TABLE ONLY public.historial_contrasenas DROP CONSTRAINT historial_contrasenas_pkey;
       public                 ganadero_anwt_user    false    254                       2606    16756    ingresos ingresos_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.ingresos
    ADD CONSTRAINT ingresos_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.ingresos DROP CONSTRAINT ingresos_pkey;
       public                 ganadero_anwt_user    false    256                       2606    16777 "   inseminaciones inseminaciones_pkey 
   CONSTRAINT     `   ALTER TABLE ONLY public.inseminaciones
    ADD CONSTRAINT inseminaciones_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.inseminaciones DROP CONSTRAINT inseminaciones_pkey;
       public                 ganadero_anwt_user    false    258                       2606    16794 ,   pastizales_animales pastizales_animales_pkey 
   CONSTRAINT     j   ALTER TABLE ONLY public.pastizales_animales
    ADD CONSTRAINT pastizales_animales_pkey PRIMARY KEY (id);
 V   ALTER TABLE ONLY public.pastizales_animales DROP CONSTRAINT pastizales_animales_pkey;
       public                 ganadero_anwt_user    false    260            ^           2606    16457    pastizales pastizales_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.pastizales
    ADD CONSTRAINT pastizales_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.pastizales DROP CONSTRAINT pastizales_pkey;
       public                 ganadero_anwt_user    false    222                       2606    16814 "   registro_leche registro_leche_pkey 
   CONSTRAINT     `   ALTER TABLE ONLY public.registro_leche
    ADD CONSTRAINT registro_leche_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.registro_leche DROP CONSTRAINT registro_leche_pkey;
       public                 ganadero_anwt_user    false    262                       2606    16849 &   registro_vacunas registro_vacunas_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.registro_vacunas
    ADD CONSTRAINT registro_vacunas_pkey PRIMARY KEY (id);
 P   ALTER TABLE ONLY public.registro_vacunas DROP CONSTRAINT registro_vacunas_pkey;
       public                 ganadero_anwt_user    false    266                       2606    16876    reproduccion reproduccion_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.reproduccion
    ADD CONSTRAINT reproduccion_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.reproduccion DROP CONSTRAINT reproduccion_pkey;
       public                 ganadero_anwt_user    false    268                       2606    16896    tareas tareas_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.tareas DROP CONSTRAINT tareas_pkey;
       public                 ganadero_anwt_user    false    270            N           2606    16412    usuarios usuarios_email_key 
   CONSTRAINT     W   ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);
 E   ALTER TABLE ONLY public.usuarios DROP CONSTRAINT usuarios_email_key;
       public                 ganadero_anwt_user    false    216            P           2606    16408    usuarios usuarios_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.usuarios DROP CONSTRAINT usuarios_pkey;
       public                 ganadero_anwt_user    false    216            R           2606    16410    usuarios usuarios_username_key 
   CONSTRAINT     ]   ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_username_key UNIQUE (username);
 H   ALTER TABLE ONLY public.usuarios DROP CONSTRAINT usuarios_username_key;
       public                 ganadero_anwt_user    false    216                       2606    16918    vacuna vacuna_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.vacuna
    ADD CONSTRAINT vacuna_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.vacuna DROP CONSTRAINT vacuna_pkey;
       public                 ganadero_anwt_user    false    272                       2606    16834    vacunas vacunas_pkey 
   CONSTRAINT     R   ALTER TABLE ONLY public.vacunas
    ADD CONSTRAINT vacunas_pkey PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.vacunas DROP CONSTRAINT vacunas_pkey;
       public                 ganadero_anwt_user    false    264                       2606    16944    ventas_leche ventas_leche_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.ventas_leche
    ADD CONSTRAINT ventas_leche_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.ventas_leche DROP CONSTRAINT ventas_leche_pkey;
       public                 ganadero_anwt_user    false    274                       2606    16959 &   vitaminizaciones vitaminizaciones_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.vitaminizaciones
    ADD CONSTRAINT vitaminizaciones_pkey PRIMARY KEY (id);
 P   ALTER TABLE ONLY public.vitaminizaciones DROP CONSTRAINT vitaminizaciones_pkey;
       public                 ganadero_anwt_user    false    276            Y           1259    16972    idx_animales_condicion    INDEX     P   CREATE INDEX idx_animales_condicion ON public.animales USING btree (condicion);
 *   DROP INDEX public.idx_animales_condicion;
       public                 ganadero_anwt_user    false    220            Z           1259    16971    idx_animales_sexo    INDEX     F   CREATE INDEX idx_animales_sexo ON public.animales USING btree (sexo);
 %   DROP INDEX public.idx_animales_sexo;
       public                 ganadero_anwt_user    false    220            [           1259    16970    idx_animales_usuario    INDEX     O   CREATE INDEX idx_animales_usuario ON public.animales USING btree (usuario_id);
 (   DROP INDEX public.idx_animales_usuario;
       public                 ganadero_anwt_user    false    220            y           1259    16975    idx_gastos_fecha    INDEX     D   CREATE INDEX idx_gastos_fecha ON public.gastos USING btree (fecha);
 $   DROP INDEX public.idx_gastos_fecha;
       public                 ganadero_anwt_user    false    248            ~           1259    16974    idx_gestaciones_estado    INDEX     P   CREATE INDEX idx_gestaciones_estado ON public.gestaciones USING btree (estado);
 *   DROP INDEX public.idx_gestaciones_estado;
       public                 ganadero_anwt_user    false    252                       1259    16976    idx_ingresos_fecha    INDEX     H   CREATE INDEX idx_ingresos_fecha ON public.ingresos USING btree (fecha);
 &   DROP INDEX public.idx_ingresos_fecha;
       public                 ganadero_anwt_user    false    256            \           1259    16973    idx_pastizales_estado    INDEX     N   CREATE INDEX idx_pastizales_estado ON public.pastizales USING btree (estado);
 )   DROP INDEX public.idx_pastizales_estado;
       public                 ganadero_anwt_user    false    222                       1259    16977    idx_registro_leche_fecha    INDEX     T   CREATE INDEX idx_registro_leche_fecha ON public.registro_leche USING btree (fecha);
 ,   DROP INDEX public.idx_registro_leche_fecha;
       public                 ganadero_anwt_user    false    262            L           1259    16413    idx_usuarios_cargo    INDEX     H   CREATE INDEX idx_usuarios_cargo ON public.usuarios USING btree (cargo);
 &   DROP INDEX public.idx_usuarios_cargo;
       public                 ganadero_anwt_user    false    216                       1259    16929    idx_vacuna_animal    INDEX     I   CREATE INDEX idx_vacuna_animal ON public.vacuna USING btree (animal_id);
 %   DROP INDEX public.idx_vacuna_animal;
       public                 ganadero_anwt_user    false    272                       1259    16931    idx_vacuna_estado    INDEX     F   CREATE INDEX idx_vacuna_estado ON public.vacuna USING btree (estado);
 %   DROP INDEX public.idx_vacuna_estado;
       public                 ganadero_anwt_user    false    272                       1259    16932    idx_vacuna_fecha_proxima    INDEX     T   CREATE INDEX idx_vacuna_fecha_proxima ON public.vacuna USING btree (fecha_proxima);
 ,   DROP INDEX public.idx_vacuna_fecha_proxima;
       public                 ganadero_anwt_user    false    272                       1259    16930    idx_vacuna_usuario    INDEX     K   CREATE INDEX idx_vacuna_usuario ON public.vacuna USING btree (usuario_id);
 &   DROP INDEX public.idx_vacuna_usuario;
       public                 ganadero_anwt_user    false    272                       1259    16978    idx_ventas_leche_fecha    INDEX     P   CREATE INDEX idx_ventas_leche_fecha ON public.ventas_leche USING btree (fecha);
 *   DROP INDEX public.idx_ventas_leche_fecha;
       public                 ganadero_anwt_user    false    274            Ï           2620    16934    vacuna update_vacuna_updated_at    TRIGGER        CREATE TRIGGER update_vacuna_updated_at BEFORE UPDATE ON public.vacuna FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
 8   DROP TRIGGER update_vacuna_updated_at ON public.vacuna;
       public               ganadero_anwt_user    false    272                       2606    16424 1   alarmas_enviadas alarmas_enviadas_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.alarmas_enviadas
    ADD CONSTRAINT alarmas_enviadas_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 [   ALTER TABLE ONLY public.alarmas_enviadas DROP CONSTRAINT alarmas_enviadas_usuario_id_fkey;
       public               ganadero_anwt_user    false    3408    216    218            ¡           2606    16473 2   animales_pastizal animales_pastizal_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.animales_pastizal
    ADD CONSTRAINT animales_pastizal_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 \   ALTER TABLE ONLY public.animales_pastizal DROP CONSTRAINT animales_pastizal_animal_id_fkey;
       public               ganadero_anwt_user    false    220    3416    224            ¢           2606    16478 4   animales_pastizal animales_pastizal_pastizal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.animales_pastizal
    ADD CONSTRAINT animales_pastizal_pastizal_id_fkey FOREIGN KEY (pastizal_id) REFERENCES public.pastizales(id);
 ^   ALTER TABLE ONLY public.animales_pastizal DROP CONSTRAINT animales_pastizal_pastizal_id_fkey;
       public               ganadero_anwt_user    false    222    224    3422            £           2606    16483 3   animales_pastizal animales_pastizal_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.animales_pastizal
    ADD CONSTRAINT animales_pastizal_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 ]   ALTER TABLE ONLY public.animales_pastizal DROP CONSTRAINT animales_pastizal_usuario_id_fkey;
       public               ganadero_anwt_user    false    3408    216    224                       2606    16443 !   animales animales_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.animales
    ADD CONSTRAINT animales_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 K   ALTER TABLE ONLY public.animales DROP CONSTRAINT animales_usuario_id_fkey;
       public               ganadero_anwt_user    false    3408    216    220            ¤           2606    16498 #   auditoria auditoria_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT auditoria_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 M   ALTER TABLE ONLY public.auditoria DROP CONSTRAINT auditoria_usuario_id_fkey;
       public               ganadero_anwt_user    false    226    216    3408            §           2606    16535 .   carbunco_animal carbunco_animal_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.carbunco_animal
    ADD CONSTRAINT carbunco_animal_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 X   ALTER TABLE ONLY public.carbunco_animal DROP CONSTRAINT carbunco_animal_animal_id_fkey;
       public               ganadero_anwt_user    false    3416    230    220            ¨           2606    16530 0   carbunco_animal carbunco_animal_carbunco_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.carbunco_animal
    ADD CONSTRAINT carbunco_animal_carbunco_id_fkey FOREIGN KEY (carbunco_id) REFERENCES public.carbunco(id);
 Z   ALTER TABLE ONLY public.carbunco_animal DROP CONSTRAINT carbunco_animal_carbunco_id_fkey;
       public               ganadero_anwt_user    false    230    228    3428            ¥           2606    16513     carbunco carbunco_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.carbunco
    ADD CONSTRAINT carbunco_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 J   ALTER TABLE ONLY public.carbunco DROP CONSTRAINT carbunco_animal_id_fkey;
       public               ganadero_anwt_user    false    220    3416    228            ¦           2606    16518 !   carbunco carbunco_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.carbunco
    ADD CONSTRAINT carbunco_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 K   ALTER TABLE ONLY public.carbunco DROP CONSTRAINT carbunco_usuario_id_fkey;
       public               ganadero_anwt_user    false    3408    216    228            ©           2606    16550 1   categorias_gasto categorias_gasto_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.categorias_gasto
    ADD CONSTRAINT categorias_gasto_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 [   ALTER TABLE ONLY public.categorias_gasto DROP CONSTRAINT categorias_gasto_usuario_id_fkey;
       public               ganadero_anwt_user    false    3408    232    216            ª           2606    16565 5   categorias_ingreso categorias_ingreso_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.categorias_ingreso
    ADD CONSTRAINT categorias_ingreso_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 _   ALTER TABLE ONLY public.categorias_ingreso DROP CONSTRAINT categorias_ingreso_usuario_id_fkey;
       public               ganadero_anwt_user    false    234    3408    216            «           2606    16580 -   config_alarmas config_alarmas_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.config_alarmas
    ADD CONSTRAINT config_alarmas_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 W   ALTER TABLE ONLY public.config_alarmas DROP CONSTRAINT config_alarmas_usuario_id_fkey;
       public               ganadero_anwt_user    false    216    236    3408            ¬           2606    16595 )   config_email config_email_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.config_email
    ADD CONSTRAINT config_email_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 S   ALTER TABLE ONLY public.config_email DROP CONSTRAINT config_email_usuario_id_fkey;
       public               ganadero_anwt_user    false    238    216    3408            ­           2606    16610 2   desparasitaciones desparasitaciones_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.desparasitaciones
    ADD CONSTRAINT desparasitaciones_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 \   ALTER TABLE ONLY public.desparasitaciones DROP CONSTRAINT desparasitaciones_animal_id_fkey;
       public               ganadero_anwt_user    false    220    3416    240            ®           2606    16615 3   desparasitaciones desparasitaciones_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.desparasitaciones
    ADD CONSTRAINT desparasitaciones_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 ]   ALTER TABLE ONLY public.desparasitaciones DROP CONSTRAINT desparasitaciones_usuario_id_fkey;
       public               ganadero_anwt_user    false    3408    216    240            ¯           2606    16630 #   empleados empleados_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.empleados
    ADD CONSTRAINT empleados_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 M   ALTER TABLE ONLY public.empleados DROP CONSTRAINT empleados_usuario_id_fkey;
       public               ganadero_anwt_user    false    242    3408    216            °           2606    16647    equipos equipos_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.equipos
    ADD CONSTRAINT equipos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 I   ALTER TABLE ONLY public.equipos DROP CONSTRAINT equipos_usuario_id_fkey;
       public               ganadero_anwt_user    false    216    3408    244            ±           2606    16662 *   fiebre_aftosa fiebre_aftosa_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.fiebre_aftosa
    ADD CONSTRAINT fiebre_aftosa_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 T   ALTER TABLE ONLY public.fiebre_aftosa DROP CONSTRAINT fiebre_aftosa_animal_id_fkey;
       public               ganadero_anwt_user    false    220    3416    246            ²           2606    16667 +   fiebre_aftosa fiebre_aftosa_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.fiebre_aftosa
    ADD CONSTRAINT fiebre_aftosa_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 U   ALTER TABLE ONLY public.fiebre_aftosa DROP CONSTRAINT fiebre_aftosa_usuario_id_fkey;
       public               ganadero_anwt_user    false    3408    216    246            ³           2606    16682    gastos gastos_categoria_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.gastos
    ADD CONSTRAINT gastos_categoria_id_fkey FOREIGN KEY (categoria_id) REFERENCES public.categorias_gasto(id);
 I   ALTER TABLE ONLY public.gastos DROP CONSTRAINT gastos_categoria_id_fkey;
       public               ganadero_anwt_user    false    248    3432    232            ´           2606    16687    gastos gastos_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.gastos
    ADD CONSTRAINT gastos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 G   ALTER TABLE ONLY public.gastos DROP CONSTRAINT gastos_usuario_id_fkey;
       public               ganadero_anwt_user    false    216    248    3408            µ           2606    16702 $   genealogia genealogia_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.genealogia
    ADD CONSTRAINT genealogia_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 N   ALTER TABLE ONLY public.genealogia DROP CONSTRAINT genealogia_animal_id_fkey;
       public               ganadero_anwt_user    false    3416    220    250            ¶           2606    16707 %   genealogia genealogia_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.genealogia
    ADD CONSTRAINT genealogia_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 O   ALTER TABLE ONLY public.genealogia DROP CONSTRAINT genealogia_usuario_id_fkey;
       public               ganadero_anwt_user    false    3408    216    250            ·           2606    16724 &   gestaciones gestaciones_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.gestaciones
    ADD CONSTRAINT gestaciones_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 P   ALTER TABLE ONLY public.gestaciones DROP CONSTRAINT gestaciones_animal_id_fkey;
       public               ganadero_anwt_user    false    3416    252    220            ¸           2606    16729 '   gestaciones gestaciones_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.gestaciones
    ADD CONSTRAINT gestaciones_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 Q   ALTER TABLE ONLY public.gestaciones DROP CONSTRAINT gestaciones_usuario_id_fkey;
       public               ganadero_anwt_user    false    216    252    3408            ¹           2606    16742 ;   historial_contrasenas historial_contrasenas_usuario_id_fkey    FK CONSTRAINT         ALTER TABLE ONLY public.historial_contrasenas
    ADD CONSTRAINT historial_contrasenas_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 e   ALTER TABLE ONLY public.historial_contrasenas DROP CONSTRAINT historial_contrasenas_usuario_id_fkey;
       public               ganadero_anwt_user    false    254    216    3408            º           2606    16757 #   ingresos ingresos_categoria_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.ingresos
    ADD CONSTRAINT ingresos_categoria_id_fkey FOREIGN KEY (categoria_id) REFERENCES public.categorias_ingreso(id);
 M   ALTER TABLE ONLY public.ingresos DROP CONSTRAINT ingresos_categoria_id_fkey;
       public               ganadero_anwt_user    false    234    256    3434            »           2606    16762 !   ingresos ingresos_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.ingresos
    ADD CONSTRAINT ingresos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 K   ALTER TABLE ONLY public.ingresos DROP CONSTRAINT ingresos_usuario_id_fkey;
       public               ganadero_anwt_user    false    3408    256    216            ¼           2606    16778 ,   inseminaciones inseminaciones_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.inseminaciones
    ADD CONSTRAINT inseminaciones_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 V   ALTER TABLE ONLY public.inseminaciones DROP CONSTRAINT inseminaciones_animal_id_fkey;
       public               ganadero_anwt_user    false    3416    220    258            ½           2606    16783 -   inseminaciones inseminaciones_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.inseminaciones
    ADD CONSTRAINT inseminaciones_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 W   ALTER TABLE ONLY public.inseminaciones DROP CONSTRAINT inseminaciones_usuario_id_fkey;
       public               ganadero_anwt_user    false    3408    258    216            ¾           2606    16800 6   pastizales_animales pastizales_animales_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.pastizales_animales
    ADD CONSTRAINT pastizales_animales_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 `   ALTER TABLE ONLY public.pastizales_animales DROP CONSTRAINT pastizales_animales_animal_id_fkey;
       public               ganadero_anwt_user    false    260    220    3416            ¿           2606    16795 8   pastizales_animales pastizales_animales_pastizal_id_fkey    FK CONSTRAINT         ALTER TABLE ONLY public.pastizales_animales
    ADD CONSTRAINT pastizales_animales_pastizal_id_fkey FOREIGN KEY (pastizal_id) REFERENCES public.pastizales(id);
 b   ALTER TABLE ONLY public.pastizales_animales DROP CONSTRAINT pastizales_animales_pastizal_id_fkey;
       public               ganadero_anwt_user    false    260    222    3422                        2606    16458 %   pastizales pastizales_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.pastizales
    ADD CONSTRAINT pastizales_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 O   ALTER TABLE ONLY public.pastizales DROP CONSTRAINT pastizales_usuario_id_fkey;
       public               ganadero_anwt_user    false    216    222    3408            À           2606    16815 ,   registro_leche registro_leche_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.registro_leche
    ADD CONSTRAINT registro_leche_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 V   ALTER TABLE ONLY public.registro_leche DROP CONSTRAINT registro_leche_animal_id_fkey;
       public               ganadero_anwt_user    false    262    220    3416            Á           2606    16820 -   registro_leche registro_leche_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.registro_leche
    ADD CONSTRAINT registro_leche_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 W   ALTER TABLE ONLY public.registro_leche DROP CONSTRAINT registro_leche_usuario_id_fkey;
       public               ganadero_anwt_user    false    216    262    3408            Ã           2606    16850 0   registro_vacunas registro_vacunas_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.registro_vacunas
    ADD CONSTRAINT registro_vacunas_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 Z   ALTER TABLE ONLY public.registro_vacunas DROP CONSTRAINT registro_vacunas_animal_id_fkey;
       public               ganadero_anwt_user    false    220    266    3416            Ä           2606    16860 1   registro_vacunas registro_vacunas_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.registro_vacunas
    ADD CONSTRAINT registro_vacunas_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 [   ALTER TABLE ONLY public.registro_vacunas DROP CONSTRAINT registro_vacunas_usuario_id_fkey;
       public               ganadero_anwt_user    false    216    266    3408            Å           2606    16855 0   registro_vacunas registro_vacunas_vacuna_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.registro_vacunas
    ADD CONSTRAINT registro_vacunas_vacuna_id_fkey FOREIGN KEY (vacuna_id) REFERENCES public.vacunas(id);
 Z   ALTER TABLE ONLY public.registro_vacunas DROP CONSTRAINT registro_vacunas_vacuna_id_fkey;
       public               ganadero_anwt_user    false    264    266    3468            Æ           2606    16877 (   reproduccion reproduccion_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.reproduccion
    ADD CONSTRAINT reproduccion_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 R   ALTER TABLE ONLY public.reproduccion DROP CONSTRAINT reproduccion_animal_id_fkey;
       public               ganadero_anwt_user    false    220    268    3416            Ç           2606    16882 )   reproduccion reproduccion_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.reproduccion
    ADD CONSTRAINT reproduccion_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 S   ALTER TABLE ONLY public.reproduccion DROP CONSTRAINT reproduccion_usuario_id_fkey;
       public               ganadero_anwt_user    false    216    3408    268            È           2606    16897    tareas tareas_empleado_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_empleado_id_fkey FOREIGN KEY (empleado_id) REFERENCES public.empleados(id);
 H   ALTER TABLE ONLY public.tareas DROP CONSTRAINT tareas_empleado_id_fkey;
       public               ganadero_anwt_user    false    270    3442    242            É           2606    16902    tareas tareas_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 G   ALTER TABLE ONLY public.tareas DROP CONSTRAINT tareas_usuario_id_fkey;
       public               ganadero_anwt_user    false    270    216    3408            Ê           2606    16919    vacuna vacuna_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.vacuna
    ADD CONSTRAINT vacuna_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 F   ALTER TABLE ONLY public.vacuna DROP CONSTRAINT vacuna_animal_id_fkey;
       public               ganadero_anwt_user    false    272    220    3416            Ë           2606    16924    vacuna vacuna_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.vacuna
    ADD CONSTRAINT vacuna_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 G   ALTER TABLE ONLY public.vacuna DROP CONSTRAINT vacuna_usuario_id_fkey;
       public               ganadero_anwt_user    false    272    216    3408            Â           2606    16835    vacunas vacunas_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.vacunas
    ADD CONSTRAINT vacunas_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 I   ALTER TABLE ONLY public.vacunas DROP CONSTRAINT vacunas_usuario_id_fkey;
       public               ganadero_anwt_user    false    3408    264    216            Ì           2606    16945 )   ventas_leche ventas_leche_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.ventas_leche
    ADD CONSTRAINT ventas_leche_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 S   ALTER TABLE ONLY public.ventas_leche DROP CONSTRAINT ventas_leche_usuario_id_fkey;
       public               ganadero_anwt_user    false    274    3408    216            Í           2606    16960 0   vitaminizaciones vitaminizaciones_animal_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.vitaminizaciones
    ADD CONSTRAINT vitaminizaciones_animal_id_fkey FOREIGN KEY (animal_id) REFERENCES public.animales(id);
 Z   ALTER TABLE ONLY public.vitaminizaciones DROP CONSTRAINT vitaminizaciones_animal_id_fkey;
       public               ganadero_anwt_user    false    276    220    3416            Î           2606    16965 1   vitaminizaciones vitaminizaciones_usuario_id_fkey    FK CONSTRAINT        ALTER TABLE ONLY public.vitaminizaciones
    ADD CONSTRAINT vitaminizaciones_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 [   ALTER TABLE ONLY public.vitaminizaciones DROP CONSTRAINT vitaminizaciones_usuario_id_fkey;
       public               ganadero_anwt_user    false    216    3408    276           